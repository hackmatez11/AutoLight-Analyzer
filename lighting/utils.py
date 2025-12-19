"""
Utility functions for CAD parsing, lighting calculations, and report generation
"""
import os
import csv
import ezdxf
from decimal import Decimal
from collections import defaultdict
from typing import Dict, List, Tuple, Optional
from datetime import datetime

from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from .models import LightingCatalog, CADFile, Room, Fixture, Report


def parse_cad(file_path: str) -> Dict:
    """
    Parse CAD file (.dwg or .dxf) and extract lighting fixture information
    
    Args:
        file_path: Path to the CAD file
        
    Returns:
        Dictionary containing parsed data with blocks, coordinates, and metadata
    """
    try:
        # Read DXF/DWG file
        doc = ezdxf.readfile(file_path)
        modelspace = doc.modelspace()
        
        # Extract block inserts (typically used for lighting fixtures)
        blocks = []
        for entity in modelspace.query('INSERT'):
            block_data = {
                'block_name': entity.dxf.name,
                'x': entity.dxf.insert.x,
                'y': entity.dxf.insert.y,
                'z': entity.dxf.insert.z if hasattr(entity.dxf.insert, 'z') else 0,
                'rotation': entity.dxf.rotation if hasattr(entity.dxf, 'rotation') else 0,
                'layer': entity.dxf.layer,
            }
            blocks.append(block_data)
        
        # Extract polylines and closed shapes (for room boundaries)
        rooms_data = []
        for entity in modelspace.query('LWPOLYLINE'):
            if entity.closed:
                points = list(entity.get_points())
                area = calculate_polyline_area(points)
                rooms_data.append({
                    'points': points,
                    'area': area,
                    'layer': entity.dxf.layer,
                })
        
        return {
            'blocks': blocks,
            'rooms': rooms_data,
            'total_blocks': len(blocks),
            'total_rooms': len(rooms_data),
            'success': True,
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'blocks': [],
            'rooms': [],
        }


def calculate_polyline_area(points: List[Tuple[float, float]]) -> float:
    """
    Calculate area of a closed polyline using the Shoelace formula
    
    Args:
        points: List of (x, y) coordinate tuples
        
    Returns:
        Area in square units
    """
    if len(points) < 3:
        return 0.0
    
    area = 0.0
    for i in range(len(points)):
        j = (i + 1) % len(points)
        area += points[i][0] * points[j][1]
        area -= points[j][0] * points[i][1]
    
    return abs(area) / 2.0


def map_symbols_to_catalog(symbols: List[str], legend: Optional[Dict[str, str]] = None) -> Dict[str, LightingCatalog]:
    """
    Map CAD block symbols to lighting catalog entries
    
    Args:
        symbols: List of unique block names from CAD
        legend: Optional dictionary mapping CAD symbols to catalog symbol_names
        
    Returns:
        Dictionary mapping CAD symbols to LightingCatalog objects
    """
    mapping = {}
    
    for symbol in symbols:
        # Try to find exact match first
        catalog_name = legend.get(symbol, symbol) if legend else symbol
        
        try:
            catalog_item = LightingCatalog.objects.get(symbol_name=catalog_name)
            mapping[symbol] = catalog_item
        except LightingCatalog.DoesNotExist:
            # Try fuzzy matching
            similar = LightingCatalog.objects.filter(symbol_name__icontains=symbol[:3])
            if similar.exists():
                mapping[symbol] = similar.first()
            else:
                # Return None for unmapped symbols
                mapping[symbol] = None
    
    return mapping


def calculate_required_fixtures(room_area: float, lumens_per_fixture: int, required_lux: float = 300) -> int:
    """
    Calculate number of fixtures required to achieve target lux level
    
    Args:
        room_area: Room area in square meters
        lumens_per_fixture: Light output per fixture in lumens
        required_lux: Target illuminance in lux (default: 300)
        
    Returns:
        Number of fixtures required
    """
    if lumens_per_fixture <= 0:
        return 0
    
    # Apply lighting efficiency factor (accounting for losses)
    efficiency_factor = 0.7
    
    total_lumens_required = room_area * required_lux
    effective_lumens_per_fixture = lumens_per_fixture * efficiency_factor
    
    fixtures_needed = total_lumens_required / effective_lumens_per_fixture
    
    # Round up to ensure adequate lighting
    import math
    return math.ceil(fixtures_needed)


def calculate_room_lux(fixtures_list: List[Fixture], room_area: float) -> float:
    """
    Calculate average lux in a room based on installed fixtures
    
    Args:
        fixtures_list: List of Fixture objects in the room
        room_area: Room area in square meters
        
    Returns:
        Average illuminance in lux
    """
    if room_area <= 0:
        return 0.0
    
    total_lumens = sum(fixture.total_lumens for fixture in fixtures_list)
    
    # Apply lighting efficiency factor
    efficiency_factor = 0.7
    effective_lumens = total_lumens * efficiency_factor
    
    return effective_lumens / room_area


def process_cad_file(cad_file: CADFile, legend: Optional[Dict[str, str]] = None) -> bool:
    """
    Process uploaded CAD file and create Room and Fixture entries
    
    Args:
        cad_file: CADFile model instance
        legend: Optional mapping of CAD symbols to catalog entries
        
    Returns:
        True if processing successful, False otherwise
    """
    try:
        # Update status
        cad_file.status = 'processing'
        cad_file.save()
        
        # Parse CAD file
        file_path = cad_file.file.path
        parsed_data = parse_cad(file_path)
        
        if not parsed_data['success']:
            cad_file.status = 'failed'
            cad_file.error_message = parsed_data.get('error', 'Unknown error')
            cad_file.save()
            return False
        
        # Create rooms
        rooms_data = parsed_data['rooms']
        if not rooms_data:
            # Create a default room if no rooms detected
            room = Room.objects.create(
                cad_file=cad_file,
                name="Main Area",
                area=100.0,  # Default area
                height=3.0,
            )
        else:
            for idx, room_data in enumerate(rooms_data):
                room = Room.objects.create(
                    cad_file=cad_file,
                    name=f"Room {idx + 1}" if idx > 0 else "Main Area",
                    area=room_data['area'],
                    height=3.0,
                )
        
        # Group blocks by name and count
        blocks_data = parsed_data['blocks']
        block_counts = defaultdict(list)
        for block in blocks_data:
            block_counts[block['block_name']].append(block)
        
        # Map symbols to catalog
        unique_symbols = list(block_counts.keys())
        symbol_mapping = map_symbols_to_catalog(unique_symbols, legend)
        
        # Create fixtures for first room (simplified)
        rooms = cad_file.rooms.all()
        if rooms.exists():
            room = rooms.first()
            
            for symbol, blocks in block_counts.items():
                catalog_item = symbol_mapping.get(symbol)
                if catalog_item:
                    # Create fixture with aggregate quantity
                    Fixture.objects.create(
                        room=room,
                        lighting_catalog=catalog_item,
                        quantity=len(blocks),
                        x_coordinate=blocks[0]['x'],
                        y_coordinate=blocks[0]['y'],
                    )
        
        # Update status
        cad_file.status = 'completed'
        cad_file.processed_at = datetime.now()
        cad_file.save()
        
        return True
        
    except Exception as e:
        cad_file.status = 'failed'
        cad_file.error_message = str(e)
        cad_file.save()
        return False


def generate_pdf_report(cad_file: CADFile) -> str:
    """
    Generate PDF report for a CAD file with lighting analysis
    
    Args:
        cad_file: CADFile model instance
        
    Returns:
        Path to generated PDF file
    """
    # Create reports directory
    report_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
    os.makedirs(report_dir, exist_ok=True)
    
    # Generate filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"lighting_report_{cad_file.id}_{timestamp}.pdf"
    filepath = os.path.join(report_dir, filename)
    
    # Create PDF
    doc = SimpleDocTemplate(filepath, pagesize=A4)
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a5490'),
        spaceAfter=30,
        alignment=TA_CENTER,
    )
    story.append(Paragraph("AutoLight Analyser Report", title_style))
    story.append(Spacer(1, 0.3 * inch))
    
    # Project info
    project_info = [
        ['Project:', cad_file.project_name],
        ['File:', cad_file.filename],
        ['Date:', cad_file.uploaded_at.strftime('%Y-%m-%d %H:%M')],
        ['User:', cad_file.user.get_full_name() or cad_file.user.username],
    ]
    
    info_table = Table(project_info, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.grey),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (1, 0), (1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.5 * inch))
    
    # Room-by-room analysis
    story.append(Paragraph("Lighting Analysis by Room", styles['Heading2']))
    story.append(Spacer(1, 0.2 * inch))
    
    total_fixtures = 0
    total_cost = Decimal('0.00')
    
    for room in cad_file.rooms.all():
        # Room header
        story.append(Paragraph(f"<b>{room.name}</b>", styles['Heading3']))
        
        room_data = [
            ['Area:', f"{room.area:.2f} m²"],
            ['Height:', f"{room.height:.2f} m"],
            ['Required Lux:', f"{room.required_lux:.0f} lux"],
            ['Current Lux:', f"{room.current_lux:.0f} lux"],
            ['Status:', 'Adequate' if room.is_adequately_lit else 'Insufficient'],
        ]
        
        room_table = Table(room_data, colWidths=[2*inch, 3*inch])
        room_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(room_table)
        story.append(Spacer(1, 0.2 * inch))
        
        # Fixtures table
        if room.fixtures.exists():
            fixture_data = [['Fixture', 'Quantity', 'Lumens/Unit', 'Total Lumens', 'Unit Cost', 'Total Cost']]
            
            for fixture in room.fixtures.all():
                fixture_data.append([
                    fixture.lighting_catalog.symbol_name,
                    str(fixture.quantity),
                    str(fixture.lighting_catalog.lumens),
                    str(fixture.total_lumens),
                    f"${fixture.lighting_catalog.unit_cost:.2f}",
                    f"${fixture.total_cost:.2f}",
                ])
                total_fixtures += fixture.quantity
                total_cost += fixture.total_cost
            
            fixture_table = Table(fixture_data, colWidths=[1.8*inch, 0.8*inch, 0.9*inch, 1*inch, 0.8*inch, 0.9*inch])
            fixture_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            story.append(fixture_table)
        else:
            story.append(Paragraph("<i>No fixtures installed in this room</i>", styles['Italic']))
        
        story.append(Spacer(1, 0.3 * inch))
    
    # Summary
    story.append(PageBreak())
    story.append(Paragraph("Project Summary", styles['Heading2']))
    story.append(Spacer(1, 0.2 * inch))
    
    summary_data = [
        ['Total Rooms:', str(cad_file.rooms.count())],
        ['Total Fixtures:', str(total_fixtures)],
        ['Total Project Cost:', f"${total_cost:.2f}"],
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 3*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#1a5490')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ('GRID', (0, 0), (-1, -1), 2, colors.black),
    ]))
    story.append(summary_table)
    
    # Build PDF
    doc.build(story)
    
    return filepath


def generate_csv_report(cad_file: CADFile) -> str:
    """
    Generate CSV report for a CAD file with lighting analysis
    
    Args:
        cad_file: CADFile model instance
        
    Returns:
        Path to generated CSV file
    """
    # Create reports directory
    report_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
    os.makedirs(report_dir, exist_ok=True)
    
    # Generate filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"lighting_report_{cad_file.id}_{timestamp}.csv"
    filepath = os.path.join(report_dir, filename)
    
    # Write CSV
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Header
        writer.writerow(['AutoLight Analyser Report'])
        writer.writerow(['Project:', cad_file.project_name])
        writer.writerow(['File:', cad_file.filename])
        writer.writerow(['Date:', cad_file.uploaded_at.strftime('%Y-%m-%d %H:%M')])
        writer.writerow(['User:', cad_file.user.get_full_name() or cad_file.user.username])
        writer.writerow([])
        
        # Room-by-room data
        for room in cad_file.rooms.all():
            writer.writerow([f'Room: {room.name}'])
            writer.writerow(['Area (m²)', 'Height (m)', 'Required Lux', 'Current Lux', 'Status'])
            writer.writerow([
                f"{room.area:.2f}",
                f"{room.height:.2f}",
                f"{room.required_lux:.0f}",
                f"{room.current_lux:.0f}",
                'Adequate' if room.is_adequately_lit else 'Insufficient'
            ])
            writer.writerow([])
            
            # Fixtures
            writer.writerow(['Fixture', 'Quantity', 'Lumens/Unit', 'Total Lumens', 'Unit Cost', 'Total Cost'])
            for fixture in room.fixtures.all():
                writer.writerow([
                    fixture.lighting_catalog.symbol_name,
                    fixture.quantity,
                    fixture.lighting_catalog.lumens,
                    fixture.total_lumens,
                    f"{fixture.lighting_catalog.unit_cost:.2f}",
                    f"{fixture.total_cost:.2f}",
                ])
            writer.writerow([])
        
        # Summary
        total_fixtures = sum(room.fixtures.count() for room in cad_file.rooms.all())
        total_cost = sum(
            fixture.total_cost
            for room in cad_file.rooms.all()
            for fixture in room.fixtures.all()
        )
        
        writer.writerow(['Summary'])
        writer.writerow(['Total Rooms', cad_file.rooms.count()])
        writer.writerow(['Total Fixtures', total_fixtures])
        writer.writerow(['Total Cost', f"{total_cost:.2f}"])
    
    return filepath

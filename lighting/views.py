"""
Views for AutoLight Analyser application
"""
import json
import os
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.http import JsonResponse, FileResponse, Http404
from django.db.models import Sum, Avg, Count
from django.views.decorators.http import require_http_methods
from django.conf import settings

from .models import CADFile, Room, Fixture, LightingCatalog, Report
from .utils import process_cad_file, generate_pdf_report, generate_csv_report
from .forms import CADUploadForm, UserRegistrationForm


@login_required
def dashboard(request):
    """
    Main dashboard showing project overview and analytics
    """
    # Get user's projects
    user_projects = CADFile.objects.filter(user=request.user, status='completed').order_by('-uploaded_at')[:10]
    
    # Calculate summary statistics
    total_projects = CADFile.objects.filter(user=request.user, status='completed').count()
    total_fixtures = Fixture.objects.filter(room__cad_file__user=request.user).aggregate(
        total=Sum('quantity')
    )['total'] or 0
    
    # Calculate average lux across all rooms
    rooms = Room.objects.filter(cad_file__user=request.user, cad_file__status='completed')
    avg_lux = sum(room.current_lux for room in rooms) / rooms.count() if rooms.count() > 0 else 0
    
    # Prepare chart data
    # Fixtures per room chart
    fixtures_per_room = []
    for project in user_projects[:5]:  # Latest 5 projects
        for room in project.rooms.all():
            fixture_count = room.fixtures.aggregate(total=Sum('quantity'))['total'] or 0
            fixtures_per_room.append({
                'room': f"{project.project_name} - {room.name}",
                'count': fixture_count
            })
    
    # Fixture types distribution
    fixture_types = Fixture.objects.filter(
        room__cad_file__user=request.user
    ).values('lighting_catalog__symbol_name').annotate(
        total=Sum('quantity')
    ).order_by('-total')[:10]
    
    # Lux trends per project
    lux_trends = []
    for project in user_projects[:10]:
        rooms = project.rooms.all()
        avg_project_lux = sum(room.current_lux for room in rooms) / rooms.count() if rooms.count() > 0 else 0
        lux_trends.append({
            'project': project.project_name,
            'lux': round(avg_project_lux, 2)
        })
    
    # Calculate total costs per project
    project_costs = []
    for project in user_projects:
        total_cost = Decimal('0.00')
        for room in project.rooms.all():
            for fixture in room.fixtures.all():
                total_cost += fixture.total_cost
        project_costs.append(total_cost)
    
    context = {
        'total_projects': total_projects,
        'total_fixtures': total_fixtures,
        'avg_lux': round(avg_lux, 2),
        'projects': zip(user_projects, project_costs),
        'fixtures_per_room': json.dumps(fixtures_per_room),
        'fixture_types': json.dumps(list(fixture_types)),
        'lux_trends': json.dumps(lux_trends),
    }
    
    return render(request, 'lighting/dashboard.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def upload_cad(request):
    """
    Handle CAD file upload
    """
    if request.method == 'POST':
        form = CADUploadForm(request.POST, request.FILES)
        if form.is_valid():
            cad_file = form.save(commit=False)
            cad_file.user = request.user
            cad_file.filename = request.FILES['file'].name
            cad_file.save()
            
            # Process the file
            try:
                # Get legend from form if provided
                legend = form.cleaned_data.get('legend')
                success = process_cad_file(cad_file, legend)
                
                if success:
                    messages.success(request, 'CAD file uploaded and processed successfully!')
                    return redirect('lighting:results', cad_id=cad_file.id)
                else:
                    messages.error(request, f'Error processing CAD file: {cad_file.error_message}')
            except Exception as e:
                messages.error(request, f'Error processing file: {str(e)}')
                cad_file.status = 'failed'
                cad_file.error_message = str(e)
                cad_file.save()
    else:
        form = CADUploadForm()
    
    return render(request, 'lighting/upload.html', {'form': form})


@login_required
def results(request, cad_id):
    """
    Display analysis results for uploaded CAD file
    """
    cad_file = get_object_or_404(CADFile, id=cad_id, user=request.user)
    
    # Get all rooms and fixtures
    rooms = cad_file.rooms.all()
    
    # Prepare data for display
    lights = []
    total_price = Decimal('0.00')
    
    for room in rooms:
        for fixture in room.fixtures.all():
            # Get recommendations (alternative fixtures with similar specs)
            recommendations = LightingCatalog.objects.filter(
                lumens__gte=fixture.lighting_catalog.lumens * 0.8,
                lumens__lte=fixture.lighting_catalog.lumens * 1.2,
            ).exclude(id=fixture.lighting_catalog.id)[:3]
            
            light_data = {
                'room': room.name,
                'dxf_block_name': fixture.lighting_catalog.symbol_name,
                'selected': fixture.lighting_catalog,
                'quantity': fixture.quantity,
                'unit_price': fixture.lighting_catalog.unit_cost,
                'total_price': fixture.total_cost,
                'recommendations': recommendations,
            }
            lights.append(light_data)
            total_price += fixture.total_cost
    
    context = {
        'cad_file': cad_file,
        'lights': lights,
        'total_price': total_price,
        'rooms': rooms,
    }
    
    return render(request, 'lighting/results.html', context)


@login_required
def generate_report(request, cad_id, report_type):
    """
    Generate and download report (PDF or CSV)
    """
    cad_file = get_object_or_404(CADFile, id=cad_id, user=request.user)
    
    try:
        if report_type == 'pdf':
            file_path = generate_pdf_report(cad_file)
            content_type = 'application/pdf'
        elif report_type == 'csv':
            file_path = generate_csv_report(cad_file)
            content_type = 'text/csv'
        else:
            raise Http404("Invalid report type")
        
        # Save report reference
        Report.objects.create(
            cad_file=cad_file,
            report_type=report_type,
            file_path=file_path
        )
        
        # Serve file
        response = FileResponse(open(file_path, 'rb'), content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
        return response
        
    except Exception as e:
        messages.error(request, f'Error generating report: {str(e)}')
        return redirect('lighting:results', cad_id=cad_id)


@login_required
def project_detail(request, cad_id):
    """
    Detailed view of a specific project
    """
    cad_file = get_object_or_404(CADFile, id=cad_id, user=request.user)
    rooms = cad_file.rooms.all()
    
    # Calculate totals
    total_fixtures = sum(fixture.quantity for room in rooms for fixture in room.fixtures.all())
    total_cost = sum(fixture.total_cost for room in rooms for fixture in room.fixtures.all())
    
    context = {
        'cad_file': cad_file,
        'rooms': rooms,
        'total_fixtures': total_fixtures,
        'total_cost': total_cost,
    }
    
    return render(request, 'lighting/project_detail.html', context)


@login_required
def update_fixture_selection(request):
    """
    AJAX endpoint to update fixture selection with alternative
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            fixture_id = data.get('fixture_id')
            new_catalog_id = data.get('catalog_id')
            
            fixture = get_object_or_404(Fixture, id=fixture_id, room__cad_file__user=request.user)
            new_catalog = get_object_or_404(LightingCatalog, id=new_catalog_id)
            
            # Update fixture
            fixture.lighting_catalog = new_catalog
            fixture.save()
            
            return JsonResponse({
                'success': True,
                'new_total_price': float(fixture.total_cost),
                'unit_price': float(new_catalog.unit_cost),
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


def register(request):
    """
    User registration view
    """
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            
            # Assign default role (Architect)
            from django.contrib.auth.models import Group
            group, created = Group.objects.get_or_create(name='Architect')
            user.groups.add(group)
            
            # Log the user in
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('lighting:dashboard')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'lighting/register.html', {'form': form})


def catalog_list(request):
    """
    Display lighting catalog
    """
    catalog_items = LightingCatalog.objects.all().order_by('symbol_name')
    
    context = {
        'catalog_items': catalog_items,
    }
    
    return render(request, 'lighting/catalog.html', context)

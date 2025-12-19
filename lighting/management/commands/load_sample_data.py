"""
Management command to load sample lighting catalog data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from lighting.models import LightingCatalog
from decimal import Decimal


class Command(BaseCommand):
    help = 'Load sample lighting catalog data and create user groups'

    def handle(self, *args, **kwargs):
        self.stdout.write('Loading sample data...')
        
        # Create user groups
        groups = ['Admin', 'Architect', 'Vendor']
        for group_name in groups:
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created group: {group_name}'))
        
        # Create sample lighting fixtures
        fixtures = [
            {
                'symbol_name': 'LED_PANEL_600X600',
                'model_number': 'LP-600-40W',
                'brand': 'Philips',
                'lumens': 4000,
                'wattage': 40.0,
                'beam_angle': 120.0,
                'color_temp': 4000,
                'unit_cost': Decimal('89.99'),
            },
            {
                'symbol_name': 'DOWNLIGHT_12W',
                'model_number': 'DL-12W-CCT',
                'brand': 'Osram',
                'lumens': 1200,
                'wattage': 12.0,
                'beam_angle': 60.0,
                'color_temp': 3000,
                'unit_cost': Decimal('34.99'),
            },
            {
                'symbol_name': 'TRACKLIGHT_20W',
                'model_number': 'TL-20W-ADJ',
                'brand': 'GE Lighting',
                'lumens': 2000,
                'wattage': 20.0,
                'beam_angle': 30.0,
                'color_temp': 3500,
                'unit_cost': Decimal('54.99'),
            },
            {
                'symbol_name': 'LINEAR_LED_40W',
                'model_number': 'LL-1200-40W',
                'brand': 'Philips',
                'lumens': 4800,
                'wattage': 40.0,
                'beam_angle': 110.0,
                'color_temp': 4000,
                'unit_cost': Decimal('79.99'),
            },
            {
                'symbol_name': 'HIGHBAY_150W',
                'model_number': 'HB-150W-IP65',
                'brand': 'Cree',
                'lumens': 18000,
                'wattage': 150.0,
                'beam_angle': 90.0,
                'color_temp': 5000,
                'unit_cost': Decimal('189.99'),
            },
            {
                'symbol_name': 'PANEL_300X1200',
                'model_number': 'LP-1200-48W',
                'brand': 'Osram',
                'lumens': 5200,
                'wattage': 48.0,
                'beam_angle': 120.0,
                'color_temp': 4000,
                'unit_cost': Decimal('99.99'),
            },
            {
                'symbol_name': 'DOWNLIGHT_8W',
                'model_number': 'DL-8W-DIM',
                'brand': 'GE Lighting',
                'lumens': 800,
                'wattage': 8.0,
                'beam_angle': 45.0,
                'color_temp': 2700,
                'unit_cost': Decimal('24.99'),
            },
            {
                'symbol_name': 'BULKHEAD_18W',
                'model_number': 'BH-18W-IP54',
                'brand': 'Philips',
                'lumens': 1800,
                'wattage': 18.0,
                'beam_angle': 180.0,
                'color_temp': 4000,
                'unit_cost': Decimal('44.99'),
            },
            {
                'symbol_name': 'STRIP_14W',
                'model_number': 'LS-600-14W',
                'brand': 'Osram',
                'lumens': 1400,
                'wattage': 14.0,
                'beam_angle': 120.0,
                'color_temp': 3000,
                'unit_cost': Decimal('29.99'),
            },
            {
                'symbol_name': 'FLOODLIGHT_50W',
                'model_number': 'FL-50W-IP66',
                'brand': 'Cree',
                'lumens': 6000,
                'wattage': 50.0,
                'beam_angle': 90.0,
                'color_temp': 5000,
                'unit_cost': Decimal('69.99'),
            },
        ]
        
        for fixture_data in fixtures:
            fixture, created = LightingCatalog.objects.get_or_create(
                symbol_name=fixture_data['symbol_name'],
                defaults=fixture_data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created fixture: {fixture.symbol_name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Fixture already exists: {fixture.symbol_name}')
                )
        
        # Create a demo user if it doesn't exist
        if not User.objects.filter(username='demo').exists():
            demo_user = User.objects.create_user(
                username='demo',
                email='demo@autolightanalyser.com',
                password='demo1234',
                first_name='Demo',
                last_name='User'
            )
            architect_group = Group.objects.get(name='Architect')
            demo_user.groups.add(architect_group)
            self.stdout.write(
                self.style.SUCCESS('Created demo user: demo / demo1234')
            )
        
        self.stdout.write(
            self.style.SUCCESS('Successfully loaded sample data!')
        )

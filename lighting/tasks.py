"""
Celery tasks for async processing
Optional: Uncomment to enable background processing
"""
from celery import shared_task
from .models import CADFile
from .utils import process_cad_file


# Uncomment to enable async CAD processing
# @shared_task
# def process_cad_file_async(cad_file_id, legend=None):
#     """
#     Process CAD file asynchronously
#     
#     Args:
#         cad_file_id: ID of CADFile to process
#         legend: Optional symbol mapping dictionary
#     
#     Returns:
#         bool: True if successful, False otherwise
#     """
#     try:
#         cad_file = CADFile.objects.get(id=cad_file_id)
#         return process_cad_file(cad_file, legend)
#     except CADFile.DoesNotExist:
#         return False
#     except Exception as e:
#         print(f"Error processing CAD file {cad_file_id}: {str(e)}")
#         return False


# Example usage in views.py:
# from .tasks import process_cad_file_async
# 
# # In upload_cad view, replace:
# # success = process_cad_file(cad_file, legend)
# # with:
# # process_cad_file_async.delay(cad_file.id, legend)

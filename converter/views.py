import os
import threading
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from .models import ConversionTask
from .utils import convert_word_to_pdf, cleanup_old_files

def home(request):
    """Main page with upload form"""
    return render(request, 'converter/index.html')

@csrf_exempt
@require_http_methods(["POST"])
def upload_and_convert(request):
    """Handle file upload and start conversion"""
    try:
        if 'file' not in request.FILES:
            return JsonResponse({'error': 'No file provided'}, status=400)
        
        file = request.FILES['file']
        
        # Validate file type
        allowed_extensions = ['.doc', '.docx']
        file_extension = os.path.splitext(file.name)[1].lower()
        if file_extension not in allowed_extensions:
            return JsonResponse({'error': 'Only .doc and .docx files are allowed'}, status=400)
        
        # Validate file size (50MB limit)
        if file.size > 50 * 1024 * 1024:
            return JsonResponse({'error': 'File size must be less than 50MB'}, status=400)
        
        # Create conversion task
        task = ConversionTask.objects.create(original_file=file)
        task.status = 'processing'
        task.save()
        
        # Start conversion in background thread
        thread = threading.Thread(target=process_conversion, args=(task.id,))
        thread.daemon = True
        thread.start()
        
        return JsonResponse({
            'task_id': str(task.id),
            'status': 'processing',
            'message': 'Conversion started'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def process_conversion(task_id):
    """Background task to process conversion"""
    try:
        task = ConversionTask.objects.get(id=task_id)
        
        def progress_callback(progress):
            task.progress = progress
            task.save()
        
        # Generate output filename
        input_filename = os.path.basename(task.original_file.name)
        output_filename = os.path.splitext(input_filename)[0] + '.pdf'
        output_path = os.path.join(settings.MEDIA_ROOT, 'outputs', output_filename)
        
        # Perform conversion
        success, message = convert_word_to_pdf(
            task.original_file.path,
            output_path,
            progress_callback
        )
        
        if success:
            task.status = 'completed'
            task.output_file.name = os.path.join('outputs', output_filename)
            task.message = 'Conversion completed successfully'
            task.progress = 100
        else:
            task.status = 'failed'
            task.message = message
        
        task.save()
        
    except Exception as e:
        try:
            task = ConversionTask.objects.get(id=task_id)
            task.status = 'failed'
            task.message = str(e)
            task.save()
        except:
            pass

def check_status(request, task_id):
    """Check conversion status"""
    try:
        task = get_object_or_404(ConversionTask, id=task_id)
        
        response_data = {
            'task_id': str(task.id),
            'status': task.status,
            'progress': task.progress,
            'message': task.message,
            'output_filename': task.output_filename()
        }
        
        # Only include file URL if conversion is completed
        if task.status == 'completed' and task.output_file:
            response_data['output_file'] = task.output_file.url
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def download_file(request, task_id):
    """Download converted PDF file"""
    try:
        task = get_object_or_404(ConversionTask, id=task_id)
        
        if task.status != 'completed' or not task.output_file:
            return JsonResponse({'error': 'File not ready for download'}, status=400)
        
        if not os.path.exists(task.output_file.path):
            return JsonResponse({'error': 'File not found on server'}, status=404)
        
        response = HttpResponse(task.output_file.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{task.output_filename()}"'
        return response
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["POST"])
@csrf_exempt
def cleanup(request):
    """Clean up old files"""
    try:
        cleanup_old_files(hours=1)
        return JsonResponse({'message': 'Cleanup completed'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
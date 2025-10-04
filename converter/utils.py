import os
import pythoncom
import comtypes.client
from django.conf import settings

def convert_word_to_pdf(input_path, output_path, progress_callback=None):
    """
    Convert Word document to PDF with exact formatting preservation
    """
    try:
        pythoncom.CoInitialize()
        
        if progress_callback:
            progress_callback(10)
        
        # Create Word application
        word = comtypes.client.CreateObject('Word.Application')
        word.Visible = False
        
        if progress_callback:
            progress_callback(30)
        
        # Open document with absolute path
        abs_input_path = os.path.abspath(input_path)
        doc = word.Documents.Open(abs_input_path)
        
        if progress_callback:
            progress_callback(60)
        
        # Convert to PDF using SaveAs (most reliable method)
        abs_output_path = os.path.abspath(output_path)
        doc.SaveAs(
            FileName=abs_output_path,
            FileFormat=17  # wdFormatPDF
        )
        
        if progress_callback:
            progress_callback(90)
        
        # Clean up
        doc.Close(SaveChanges=False)
        word.Quit()
        
        if progress_callback:
            progress_callback(100)
        
        return True, "Conversion successful"
        
    except Exception as e:
        return False, f"Conversion failed: {str(e)}"
    finally:
        try:
            pythoncom.CoUninitialize()
        except:
            pass

def cleanup_old_files(hours=1):
    """
    Clean up files older than specified hours
    """
    import time
    from django.core.files.storage import default_storage
    
    current_time = time.time()
    cutoff_time = current_time - (hours * 3600)
    
    # Clean uploads
    uploads_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
    if os.path.exists(uploads_dir):
        for filename in os.listdir(uploads_dir):
            file_path = os.path.join(uploads_dir, filename)
            if os.path.isfile(file_path):
                if os.path.getctime(file_path) < cutoff_time:
                    try:
                        os.remove(file_path)
                    except:
                        pass
    
    # Clean outputs
    outputs_dir = os.path.join(settings.MEDIA_ROOT, 'outputs')
    if os.path.exists(outputs_dir):
        for filename in os.listdir(outputs_dir):
            file_path = os.path.join(outputs_dir, filename)
            if os.path.isfile(file_path):
                if os.path.getctime(file_path) < cutoff_time:
                    try:
                        os.remove(file_path)
                    except:
                        pass
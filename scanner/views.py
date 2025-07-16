from django.shortcuts import render
import qrcode
from .models import QRCode
from django.core.files.storage import FileSystemStorage
from io import BytesIO
from django.core.files.base import ContentFile
from PIL import Image
import cv2
import numpy as np
from pathlib import Path
from django.conf import settings
from django.shortcuts import render
from .models import QRCode




def homepage(request):
    all_qrcodes = QRCode.objects.all().order_by('-id')  # latest first
    return render(request, 'core/homepage.html', {'qrcodes': all_qrcodes})


# QR Code Generator View
def generate_qr(request):
    qr_image_url = None
    if request.method == 'POST':
        mobile_number = request.POST.get('mobile_number')
        data = request.POST.get('qr_data')

        # Validate mobile number
        if not mobile_number or len(mobile_number) != 10 or not mobile_number.isdigit():
            return render(request, 'scanner/generate.html', {'error': 'Invalid mobile number'})

        qr_content = f"{data}|{mobile_number}"

        qr = qrcode.make(qr_content)

        qr_image_io = BytesIO()
        qr.save(qr_image_io, format='PNG')
        qr_image_io.seek(0)

        fs = FileSystemStorage(location='media/qr_codes/', base_url='/media/qr_codes/')
        filename = f"{data}_{mobile_number}.png"
        qr_image_content = ContentFile(qr_image_io.read(), name=filename)

        filepath = fs.save(filename, qr_image_content)
        qr_image_url = fs.url(filename)

        # Save to DB
        QRCode.objects.create(data=data, mobile_number=mobile_number)

        return render(request, 'scanner/generate.html', {'qr_image_url': qr_image_url})

    return render(request, 'scanner/generate.html')


# QR Code Scanner View using OpenCV
def scan_qr(request):
    result = None

    if request.method == 'POST' and request.FILES.get('qr_image'):
        mobile_number = request.POST.get('mobile_number')
        qr_image = request.FILES['qr_image']

        # Validate mobile number
        if not mobile_number or len(mobile_number) != 10 or not mobile_number.isdigit():
            return render(request, 'scanner/scanner.html', {'error': 'Invalid mobile number'})

        fs = FileSystemStorage()
        filename = fs.save(qr_image.name, qr_image)
        image_path = Path(fs.location) / filename

        try:
            # Read image and convert to OpenCV format
            image = Image.open(image_path).convert('RGB')
            image_np = np.array(image)
            image_cv = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)

            detector = cv2.QRCodeDetector()
            data, vertices, _ = detector.detectAndDecode(image_cv)

            if data:
                try:
                    qr_data, qr_mobile_number = data.strip().split('|')

                    qr_entry = QRCode.objects.filter(data=qr_data, mobile_number=qr_mobile_number).first()

                    if qr_entry and qr_mobile_number == mobile_number:
                        result = "✅ Scan Success: Valid QR code for the provided mobile number"

                        qr_entry.delete()

                        qr_image_path = Path(settings.MEDIA_ROOT) / 'qr_codes' / f"{qr_data}_{qr_mobile_number}.png"
                        if qr_image_path.exists():
                            qr_image_path.unlink()

                    else:
                        result = "❌ Scan Failed: Invalid QR code or mobile number mismatch"
                except:
                    result = "⚠️ QR Code format is incorrect"
            else:
                result = "❌ Scan Failed: No QR code detected in the image"

        except Exception as e:
            result = f"⚠️ Error processing the image: {str(e)}"

        finally:
            if image_path.exists():
                image_path.unlink()

    return render(request, 'scanner/scanner.html', {'result': result})

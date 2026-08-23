from collections import defaultdict
from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.db import transaction
from django.contrib.auth.decorators import login_required
from .models import CategoryMaster, Docma_MetaData , DocmaFile
from .google_drive_manager import GoogleDriveStorage
from django.db.models import Count

drive = GoogleDriveStorage()

# def upload(request):
#     """
#     Main entry view.
#     GET  -> render page
#     POST -> delegate to upload handler
#     """
#
#     if request.method == "POST":
#         print("request for upload files")
#         family = request.POST.get("family", "").strip()
#         holder = request.POST.get("holder", "").strip()
#         refnumber = request.POST.get("refnumber", "").strip()
#         status = request.POST.get("status", "1").strip()
#         category = request.POST.get("category", "").strip()
#         sub_category = request.POST.get("sub_category", "").strip()
#         remarks = request.POST.get("remarks", "").strip()
#         price = request.POST.get("price", 0)
#         value = request.POST.get("value", 0)
#         start_date = request.POST.get("start_date") or None
#         end_date = request.POST.get("end_date") or None
#
#         files = request.FILES.getlist("files")
#
#
#         # if not refnumber:
#         #     return JsonResponse({
#         #         "success": False,
#         #         "error": "Reference Number is required."
#         #     })
#
#
#
#         # ==========================================
#         # SAVE DOCUMENT ENTRY FIRST
#         # ==========================================
#         doc = Docma_MetaData.objects.create(
#             family=family,
#             refnumber=refnumber,
#             holder=holder,
#             category=category,
#             sub_category=sub_category,
#
#             price=price,
#             value=value,
#
#             start_date=start_date,
#             end_date=end_date,
#
#             status=status,
#             remarks=remarks,
#
#             updated_by=request.user.username if request.user.is_authenticated else "system"
#         )
#
#         # ==========================================
#         # GOOGLE DRIVE UPLOAD
#         # FOLDER STRUCTURE:
#         # DOCMA/Family/Category/SubCategory/RefNo
#         # ==========================================
#
#         folder_path = (
#             f"Aura_Docma/"
#             f"{family}"
#
#         )
#
#         upload_results = drive.upload_files(
#             files=files,
#             target_folder=folder_path
#         )
#         print(upload_results)
#         uploaded_files = []
#         uploaded_count = 0
#
#         for i, result in enumerate(upload_results):
#             if result.get("success"):
#                 uploaded_count += 1
#                 uploaded_file = files[i]
#
#                 file_record = DocmaFile.objects.create(
#                     document=doc,
#                     file_name=result.get("name", ""),
#                     file_path=f"{folder_path}/{result.get('name', '')}",
#                     file_url=result.get("image_url", ""),
#                     file_type=uploaded_file.content_type or "",
#                     file_size=uploaded_file.size or 0
#                 )
#
#                 uploaded_files.append({
#                     "id": file_record.id,
#                     "name": file_record.file_name,
#                     "url": file_record.file_url
#                 })
#
#         # ==========================================
#         # RESPONSE
#         # ==========================================
#         return JsonResponse({
#             "success": True,
#             "document_id": doc.id,
#             "files_uploaded": uploaded_count,
#             "files": uploaded_files
#         })
#
#
#     return _render_upload_page(request)  # 🔴 DELEGATION
from django.http import JsonResponse
from django.db import IntegrityError  # <-- Make sure this is imported!
import logging

logger = logging.getLogger(__name__)

from django.http import JsonResponse
from django.db import IntegrityError
import logging

logger = logging.getLogger(__name__)


def upload(request):
    """
    GET  -> render upload page
    POST -> save metadata, upload files to Google Drive, save file records
    """

    if request.method == "POST":
        family = request.POST.get("family", "").strip()
        holder = request.POST.get("holder", "").strip()
        refnumber = request.POST.get("refnumber", "").strip()
        status = request.POST.get("status", "1").strip()
        category = request.POST.get("category", "").strip()
        sub_category = request.POST.get("sub_category", "").strip()
        remarks = request.POST.get("remarks", "").strip()
        price = request.POST.get("price", 0)
        value = request.POST.get("value", 0)
        start_date = request.POST.get("start_date") or None
        end_date = request.POST.get("end_date") or None

        files = request.FILES.getlist("files")

        if not files:
            return JsonResponse({
                "success": False,
                "error": "No files received by server."
            })

        if not family:
            return JsonResponse({
                "success": False,
                "error": "Family is required."
            })

        if not holder:
            return JsonResponse({
                "success": False,
                "error": "Holder is required."
            })

        if not refnumber:
            return JsonResponse({
                "success": False,
                "error": "Reference Number is required."
            })

        if not category:
            return JsonResponse({
                "success": False,
                "error": "Category is required."
            })

        if not sub_category:
            return JsonResponse({
                "success": False,
                "error": "Sub Category is required."
            })

        try:
            doc = Docma_MetaData.objects.create(
                family=family,
                refnumber=refnumber,
                holder=holder,
                category=category,
                sub_category=sub_category,
                price=price,
                value=value,
                start_date=start_date,
                end_date=end_date,
                status=status,
                remarks=remarks,
                updated_by=request.user.username if request.user.is_authenticated else "system"
            )

        except IntegrityError:
            logger.exception("Duplicate or integrity error during document upload")
            return JsonResponse({
                "success": False,
                "error": f"A document with Reference Number '{refnumber}' already exists."
            })

        except Exception as e:
            logger.exception("Metadata save failed")
            return JsonResponse({
                "success": False,
                "error": f"Failed to initialize document profile: {str(e)}"
            })

        try:
            drive = GoogleDriveStorage()

            if not getattr(drive, "service", None):
                raise Exception("Google Drive service is not initialized. Check credentials or token setup.")

            folder_path = f"Aura_Docma/{family}"

            upload_results = drive.upload_files(
                files=files,
                target_folder=folder_path
            )

            uploaded_files = []
            uploaded_count = 0

            for index, result in enumerate(upload_results):
                if not result.get("success"):
                    continue

                uploaded_count += 1
                uploaded_file = files[index]

                file_record = DocmaFile.objects.create(
                    document=doc,
                    file_name=result.get("name", uploaded_file.name),
                    file_path=f"{folder_path}/{result.get('name', uploaded_file.name)}",
                    file_url=result.get("image_url", ""),
                    file_type=uploaded_file.content_type or "",
                    file_size=uploaded_file.size or 0
                )

                uploaded_files.append({
                    "id": file_record.id,
                    "name": file_record.file_name,
                    "url": file_record.file_url
                })

            if uploaded_count == 0:
                doc.delete()
                return JsonResponse({
                    "success": False,
                    "error": "Files were received, but none were uploaded to Google Drive."
                })

            return JsonResponse({
                "success": True,
                "document_id": doc.id,
                "files_uploaded": uploaded_count,
                "files": uploaded_files
            })

        except Exception as e:
            logger.exception("File attachment layer failed")

            try:
                doc.delete()
            except Exception:
                logger.exception("Failed to delete metadata after upload failure")

            return JsonResponse({
                "success": False,
                "error": f"File storage process failed: {str(e)}"
            })

    return _render_upload_page(request)

# =====================================================
# INTERNAL FUNCTIONS (SAME VIEW FILE)
# =====================================================
@login_required
def _render_upload_page(request):
    """
    Handles ONLY page rendering (GET)
    """

    user = request.user
    family_name = user.family_name

    # ---------- CATEGORY TREE ----------
    qs = CategoryMaster.objects.filter(
        family__in=["DEFAULT", family_name],
        status=1
    ).order_by("category", "sub_category")

    category_tree = defaultdict(list)
    for obj in qs:
        category_tree[obj.category].append(obj.sub_category)

    # ---------- HOLDERS ----------
    User = get_user_model()
    usernames = User.objects.filter(
        family_name=family_name
    ).values_list("username", flat=True)





    return render(request, "DOCMA_Upload.html", {
        "family": family_name,
        "usernames": usernames,
        "category_tree": dict(category_tree),
        "available_storage_mb":100
    })


def home_page(request):
    selected_user = request.GET.get("user", "all")

    user = request.user
    family_name = user.family_name
    print(user, user.family_name)
    User = get_user_model()
    usernames = User.objects.filter(family_name=family_name).values_list("username", flat=True)
    print(user, user.family_name)

    if selected_user == "all":
        result = Docma_MetaData.objects.filter(family=family_name).values("category").annotate(total=Count("id"))
        # data = {item["category"]: item["total"] for item in result}
    else:
        result = Docma_MetaData.objects.filter(family=family_name , holder = selected_user).values("category").annotate(
            total=Count("id"))
        # data = {item["category"]: item["total"] for item in result}

    context = {
        "users": usernames,
        "selected_user": selected_user,
        "card_data":result ,
        "mode": 3
    }

    print(context)

    return render(request, "DOCMA_HomePage.html", context)



def view_subcategory(request):

    user = request.GET.get("user", "all")
    cat = request.GET.get("cat")
    logged_user = request.user
    family_name = logged_user.family_name
    print(user, family_name)
    User = get_user_model()
    usernames = User.objects.filter(family_name=family_name).values_list("username", flat=True)

    if user == "all":
        result = Docma_MetaData.objects.filter(category=cat).values("sub_category").annotate(total=Count("id"))
    else:
        result = Docma_MetaData.objects.filter(category=cat , holder = user).values("sub_category").annotate(
            total=Count("id"))
    print(result)
    for r in result:
        print(r['sub_category'])
        img = CategoryMaster.objects.get(
            sub_category=r['sub_category'],
            category=cat
        ).icon
        print(img)
        r['img'] = img
        r['category'] = cat
    print(result)

    context = {
        "users": usernames,
        "card_data": result,
        "selected_user": user,
    }
    return render(request, "Docma_SubCategory.html" , context)

def convert_drive_url(url):
    if "id=" in url:
        file_id = url.split("id=")[-1]
        return f"https://lh3.googleusercontent.com/d/{file_id}"
    return url

def view_images(request):

    user = request.GET.get("user", "all")
    cat = request.GET.get("cat")
    sub_cat = request.GET.get("subcat")
    logged_user = request.user
    family_name = logged_user.family_name
    User = get_user_model()
    usernames = User.objects.filter(family_name=family_name).values_list("username", flat=True)
    print(user, cat, sub_cat)

    if user == "all":
        docs = Docma_MetaData.objects.filter(category= cat , sub_category = sub_cat).prefetch_related("files")
    else:
        docs = Docma_MetaData.objects.filter(category=cat , sub_category = sub_cat , holder = user).prefetch_related("files")
    result = {}
    for doc in docs:
        result[doc.id] = {
            "meta": {
                "id": doc.id,
                "family": doc.family,
                "refnumber": doc.refnumber,
                "holder": doc.holder,
                "category": doc.category,
                "sub_category": doc.sub_category,
                "ocr_text": doc.ocr_text,
                "price": doc.price,
                "value": doc.value,
                "start_date": doc.start_date,
                "end_date": doc.end_date,
                "status": doc.status,
                "remarks": doc.remarks,
                "updated_by": doc.updated_by,
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
            },
            "files": [
                {
                    "id": f.id,
                    "file_name": f.file_name,
                    "file_path": f.file_path,
                    "file_url": convert_drive_url(f.file_url),
                    "file_type": f.file_type,
                    "file_size": f.file_size,
                    "uploaded_at": f.uploaded_at.isoformat() if f.uploaded_at else None,
                }
                for f in doc.files.all()
            ]
        }

        qs = CategoryMaster.objects.filter(
        family__in=["DEFAULT", family_name],
        status=1
        ).order_by("category", "sub_category")

        category_tree = defaultdict(list)
        for obj in qs:
            category_tree[obj.category].append(obj.sub_category)

    print(category_tree)
    context = {
        "users": usernames,
        "selected_user": user,
        "category_tree": dict(category_tree),
        "result": result
    }

    return render(request, "Docma_ViewPage.html" , context)


def tester(request):
    return render(request, "Test.html" )






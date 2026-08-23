from django.db import models




class CategoryMaster(models.Model):
    """
    Master table for Category & Sub-Category
    Uses default auto-increment primary key (id)
    """

    # id = models.BigAutoField(primary_key=True)
    # ↑ This is implicit in Django, no need to declare

    family = models.CharField(
        max_length=100,
        default="DEFAULT",
        db_index=True
    )

    category = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Top level category e.g. Bank & Money"
    )

    sub_category = models.CharField(
        max_length=100,
        help_text="Sub category e.g. Credit Card"
    )

    info = models.TextField(
        blank=True,
        null=True
    )

    icon = models.ImageField(
        upload_to="DOCMA/MasterCategoryIcons/",
        blank=True,
        null=True ,
        default="DOCMA/MasterCategoryIcons/default.png"
    )

    status = models.IntegerField(
        default=1,
        help_text="1 = Active, 0 = Inactive"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("family", "category", "sub_category")
        ordering = ["category", "sub_category"]

    def __str__(self):
        return f"{self.category} → {self.sub_category}"




class Docma_MetaData(models.Model):
    """
    Main document metadata table.
    Primary Key = auto-increment id
    """

    # ---- PRIMARY KEY ----
    id = models.AutoField(primary_key=True)

    # ---- Family Scope ----
    family = models.CharField(
        max_length=100,
        default="DEFAULT",
        db_index=True,
        help_text="Family to which this document belongs"
    )

    # ---- Business Reference ----
    refnumber = models.CharField(
        max_length=200,
        unique=True,
        blank=True,
        null=True,
        db_index=True,
        help_text="External or document reference number (Aadhaar, Policy No, etc.)"
    )

    # ---- Ownership ----
    holder = models.CharField(
        max_length=200,
        help_text="Person in the family who owns this document"
    )

    # ---- Classification ----
    category = models.CharField(
        max_length=100,
        help_text="Top-level category (Bank & Money, Education, etc.)"
    )

    sub_category = models.CharField(
        max_length=100,
        help_text="Specific document type (Credit Card, Aadhaar, etc.)"
    )

    # ---- OCR / AI ----
    ocr_text = models.TextField(
        blank=True,
        null=True,
        help_text="Extracted OCR text for AI search and understanding"
    )

    # ---- Financial Fields ----
    price = models.IntegerField(
        default=0,
        help_text="Cost paid for the document (if applicable)"
    )

    value = models.IntegerField(
        default=0,
        help_text="Assessed or insured value (if applicable)"
    )

    # ---- Date Fields (OPTIONAL) ----
    start_date = models.DateField(
        blank=True,
        null=True,
        help_text="Start or issue date (if applicable)"
    )

    end_date = models.DateField(
        blank=True,
        null=True,
        help_text="End or expiry date (if applicable)"
    )

    # ---- Status ----
    status = models.IntegerField(
        default=1,
        help_text="1 = Active, 0 = Inactive, 2 = Archived"
    )

    # ---- Audit ----
    remarks = models.CharField(
        max_length=300,
        blank=True,
        help_text="Additional notes"
    )

    updated_by = models.CharField(
        max_length=200,
        help_text="User who last updated this document"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Record creation timestamp"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Record last updated timestamp"
    )

    def __str__(self):
        return f"{self.id} | {self.category} → {self.sub_category} | {self.holder}"



class DocmaFile(models.Model):

    document = models.ForeignKey(
        Docma_MetaData,
        related_name="files",
        on_delete=models.CASCADE
    )

    file_name = models.CharField(max_length=300 , default="")
    file_path = models.CharField(max_length=500 , default="")
    file_url = models.TextField( default="")
    file_type = models.CharField(max_length=100 ,default="")
    file_size = models.BigIntegerField(  default= 0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file_name

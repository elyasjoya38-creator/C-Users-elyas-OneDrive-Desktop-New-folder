from django.db import models

typelist = (
    ("Seminar", "Seminar"), ("Workshop", "Workshop"), ("Course", "Course"),
    ("Tranning", "Tranning"), ("zoomcall", "Zoom Call"),
)

class pdc_detials(models.Model):
    title = models.CharField(max_length=100)
    producer = models.CharField(max_length=100, null=True, blank=True)
    descript = models.TextField(null=True, blank=True)
    types = models.CharField(max_length=50, choices=typelist, null=True, blank=True)
    time = models.TimeField(null=True, blank=True)
    startdate = models.DateField(null=True, blank=True)
    enddate = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=100, null=True, blank=True)
    urls = models.URLField(max_length=200, null=True, blank=True)
    class Meta:
        ordering = ["-id"]
        verbose_name = "PDC record"
        verbose_name_plural = "PDC records"
    def __str__(self):
        return self.title

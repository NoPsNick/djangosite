from django.contrib import admin
from django.utils.html import format_html

from pages.models import About


# Register your models here.
@admin.register(About)
class AboutAdmin(admin.ModelAdmin):
    readonly_fields = ('admin_preview', 'created', 'modified')
    fields = (
        'position', 'admin_preview', 'image_cima', 'link_image_cima', 'title', 'link_title',
        'description', 'link_description', 'text_link_description', 'image_meio', 'link_image_meio',
        'image_baixo', 'link_image_baixo', 'last'
    )

    def admin_preview(self, obj):
        html = '<div class="container my-3">'

        # Render image_cima with link if provided
        if obj.image_cima:
            html += '<div class="w3-card-4" style="width: 100%; border-radius: 5px; overflow: hidden;">'
            if obj.link_image_cima:
                html += f'<a href="{obj.link_image_cima}" target="_blank">'
            html += f'<img class="w3-card-img-top w3-responsive w3-image" src="{obj.image_cima.url}" style="border-top-left-radius: 15px; border-top-right-radius: 15px;" />'
            if obj.link_image_cima:
                html += '</a>'

        # Render title with link if provided
        if obj.title:
            html += '<div class="w3-container w3-center">'
            if obj.link_title:
                html += f'<a href="{obj.link_title}" target="_blank">'
            html += f'<h5>{obj.title}</h5>'
            if obj.link_title:
                html += '</a>'
            html += '</div>'

        # Render image_meio with link if provided
        if obj.image_meio:
            if obj.link_image_meio:
                html += f'<a href="{obj.link_image_meio}" target="_blank">'
            html += f'<img class="w3-card-img-top w3-responsive w3-image" src="{obj.image_meio.url}" />'
            if obj.link_image_meio:
                html += '</a>'

        # Render description with link if provided
        if obj.description:
            html += '<div class="w3-container"><p>'
            html += obj.description.replace("\n", "<br>")  # Converts line breaks for HTML
            if obj.link_description:
                html += f' <a href="{obj.link_description}" style="text-decoration:none">'
                html += obj.text_link_description or 'Clique Aqui'
                html += '</a>'
            html += '</p></div>'

        # Render image_baixo with link if provided
        if obj.image_baixo:
            if obj.link_image_baixo:
                html += f'<a href="{obj.link_image_baixo}" target="_blank">'
            html += f'<img class="w3-card-img-top w3-responsive w3-image" src="{obj.image_baixo.url}" />'
            if obj.link_image_baixo:
                html += '</a>'

        html += '</div>'
        return format_html(html)

    admin_preview.short_description = "Visualização"
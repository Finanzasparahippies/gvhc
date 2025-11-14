from django.db import models
from cloudinary.models import CloudinaryField
from django.contrib.postgres.fields import ArrayField



class ResponseType(models.Model):
    type_name = models.CharField(max_length=50)  # Ej: 'Texto', 'Imagen', 'Proceso'
    description = models.TextField(blank=True)

    def __str__(self):
        return self.type_name

class Department(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Answer(models.Model):
    NODE_TYPES = [
        ('CustomResizableNode', 'Custom Resizable Node'), #images
        ('NonResizableNode', 'Non Resizable Node'), #scripts or protocols
        ('slidesToElements', 'slides To Elements'), #path of responses 
        ('TooltipNode', 'Tool tip Node'), #tips fot newbies
        ('AnnotationNode', 'Annotation Node'), #Node just to add things and they perserve on time
        ('NotesNode', 'Note Node'), #Node to take notes from an appt and save it in folders.
        ('TemplateNode', 'Template Node'), #quick answers to work
    ]
    title = models.CharField(max_length=255, blank=True, null=True)
    keywords = ArrayField(models.CharField(max_length=50), blank=True, default=list)  # Lista de palabras clave
    answer_text = models.TextField(blank=True, null=True)
    template = models.TextField(blank=True, null=True)
    has_steps = models.BooleanField(default=False)  # Indica si la respuesta tiene pasos
    image = CloudinaryField('image', blank=True, null=True)
    node_type = models.CharField(max_length=50, choices=NODE_TYPES, default='NonResizableNode')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    relevance = models.IntegerField(default=0)
    related_answers = models.ManyToManyField('self', through='AnswerConnection', symmetrical=False)
    pos_x = models.FloatField(null=True, blank=True)
    pos_y = models.FloatField(null=True, blank=True)
<<<<<<< HEAD
    is_visible = models.BooleanField(default=True)  # Nuevo campo
=======
>>>>>>> 079e3c9 (first commit)

    def __str__(self):
        return self.title[:50] if self.title else "No text available"

class Step(models.Model):
    answer = models.ForeignKey(Answer, related_name='steps', on_delete=models.CASCADE)
    keywords = ArrayField(models.CharField(max_length=50), blank=True, default=list)  # Lista de palabras clave
    number = models.PositiveIntegerField()  # Campo para el número del paso
    text = models.TextField()               # Campo para el texto del paso
    image = CloudinaryField('image', blank=True, null=True)
    excel_file = models.FileField(upload_to='steps/excel_files/', blank=True, null=True)
    pos_x = models.FloatField(null=True, blank=True)
    pos_y = models.FloatField(null=True, blank=True) 
<<<<<<< HEAD
    is_visible = models.BooleanField(default=True)  # Nuevo campo
=======
>>>>>>> 079e3c9 (first commit)


    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['answer', 'number'], name='unique_step_per_answer')
        ]

    def __str__(self):
        return f"Step {self.number} for Answer {self.answer}: {self.text[:50]}"

class AnswerConnection(models.Model):
    PATH_CHOICES = [
        ('yes', 'Yes'),
        ('no', 'No'),
    ]

    from_answer = models.ForeignKey(Answer, related_name='from_connections', on_delete=models.CASCADE)
    to_answer = models.ForeignKey(Answer, related_name='to_connections', on_delete=models.CASCADE)
    decision_path = models.CharField(max_length=20, choices=PATH_CHOICES, blank=True, null=True) 

class Event(models.Model):
    EVENT_TYPES = [
        ('PRIMORDIAL', 'Primordial'),
        ('NORMAL', 'Normal'),
    ]
    keywords = ArrayField(models.CharField(max_length=50), blank=True, default=list)  # Lista de palabras clave
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    requirements = models.TextField(blank=True)
    address = models.CharField(max_length=255, blank=True)
    hospital = models.CharField(max_length=255, blank=True)
    county = models.CharField(max_length=255, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    event_type = models.CharField(max_length=10, choices=EVENT_TYPES, default='NORMAL')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.title

class Faq(models.Model):
    CATEGORIES = [
        ('Protocols', 'Protocols'),
        ('Tips', 'Tips'),
        ('Payrolls', 'Payrolls'),
        ('Escalations', 'Escalations'),
        ('FeedBack', 'FeedBack'),
    ] 
    
    question = models.CharField(max_length=255)
    response_type = models.ForeignKey(ResponseType, on_delete=models.CASCADE, default=1)
    category = models.CharField(max_length=20, choices=CATEGORIES, default='Protocols')
    keywords = ArrayField(models.CharField(max_length=50), blank=True, default=list)  # Lista de palabras clave
    answers = models.ManyToManyField(Answer, related_name='faqs')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    events = models.ManyToManyField(Event, blank=True, related_name='events')
    pos_x = models.FloatField(null=True, blank=True)
    pos_y = models.FloatField(null=True, blank=True)
<<<<<<< HEAD
    is_visible = models.BooleanField(default=True)  # Nuevo campo
=======
>>>>>>> 079e3c9 (first commit)

    def __str__(self):
        return self.question 
    
class Slide(models.Model):
    faq = models.ForeignKey(Faq, on_delete=models.CASCADE, related_name='slides')
    question = models.TextField()  # Texto de la pregunta o contenido del slide
    left = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='left_slide')
    right = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='right_slide')
    up = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='up_slide')
    down = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='down_slide')
<<<<<<< HEAD
    is_visible = models.BooleanField(default=True)  # Nuevo campo
=======
>>>>>>> 079e3c9 (first commit)

    def __str__(self):
        return f"Slide for {self.faq} - {self.question[:50]}"

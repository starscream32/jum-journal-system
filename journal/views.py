import json
from django.shortcuts import render, get_object_or_404, redirect
from .models import Manuscript, Volume, Author, ManuscriptReview
from django.db.models import Count
from .forms import BugForm, ContactForm
from .filters import ManuscriptFilter
from django.core.mail import send_mail
from django.http import HttpResponse

def index(request):
    # This query gives the totals for each degree in a dictionary, then we pass it into the view and loop over it to
    # render the values in Chart.js.
    degree_counts = Author.objects.order_by('degree').values('degree').annotate(Count('id'))
    degree_counts = list(degree_counts)

    degree_counts_labels = []
    degree_counts_dataset = []

    for item in degree_counts:
        degree_counts_dataset.append(item['id__count'])
        degree_counts_labels.append(item['degree'])

    degree_counts_labels = json.dumps(degree_counts_labels)
    degree_counts_dataset = json.dumps(degree_counts_dataset)

    # This query gives the manuscript totals for each volume.
    m_by_volume_count = Manuscript.objects.order_by('citation_volume').values('citation_volume').annotate(Count('id'))
    m_by_volume_count = list(m_by_volume_count)
    volume_count_labels = []
    volume_count_dataset = []

    for item in m_by_volume_count:
        volume_count_labels.append(item['citation_volume'])
        volume_count_dataset.append(item['id__count'])

    volume_count_labels = json.dumps(volume_count_labels)
    volume_count_dataset = json.dumps(volume_count_dataset)

    # This query gives the manuscript totals for each section.
    section_count = Manuscript.objects.order_by('section__title').values('section__title').annotate(Count('id'))

    section_count = list(section_count)
    section_count_labels = []
    section_count_dataset = []

    for item in section_count:
        section_count_labels.append(item['section__title'])
        section_count_dataset.append(item['id__count'])

    section_count_labels = json.dumps(section_count_labels)
    section_count_dataset = json.dumps(section_count_dataset)

    manuscript_list = Manuscript.objects.all()
    manuscript_filter = ManuscriptFilter(request.GET, queryset=manuscript_list)

    # Query for all volumes
    mss = Manuscript.objects.all()
    return render(
        request,
        template_name='index.html',
        context={
            'section_count_labels': section_count_labels,
            'section_count_dataset': section_count_dataset,
            'volume_count_labels': volume_count_labels,
            'volume_count_dataset': volume_count_dataset,
            'degree_counts_labels': degree_counts_labels,
            'degree_counts_dataset': degree_counts_dataset,
            "manuscripts": mss,
            "volumes": Volume.objects.all().order_by('date'),
            'filter': manuscript_filter,
        }
    )


def charts(request):
    author_student_count = Author.objects.filter(degree='Student').count()
    author_bsc_count = Author.objects.filter(degree='Bsc').count()
    author_msc_count = Author.objects.filter(degree='Msc').count()
    author_phd_count = Author.objects.filter(degree='PhD').count()
    return render(
        request,
        template_name='statistics.html',
        context={
            "student_count": author_student_count,
            "bsc_count": author_bsc_count,
            "msc_count": author_msc_count,
            "phd_count": author_phd_count,
        }
    )


def advancedsearch(request):
    manuscript_list = Manuscript.objects.all()
    manuscript_filter = ManuscriptFilter(request.GET, queryset=manuscript_list)
    return render(
        request,
        template_name='advanced_search.html',
        context={
            'filter': manuscript_filter,
        }
    )


def abstract(request, slug_field):
    show_abstract = get_object_or_404(Manuscript, slug_field=slug_field)
    return render(request, 'abstract.html', context={
        'abstract': show_abstract,
    }
                  )


def author(request):
    show_author = get_object_or_404(Author, id=id)
    return render(request, template_name='author.html', context={
        'author': show_author,
    })


def volumeview(request, name):
    q = Volume.objects.filter().order_by('last_page')
    show_volume = get_object_or_404(q, name=name)
    show_manuscripts = Manuscript.objects.filter(citation_volume__name__exact=str(name))
    return render(request, 'volumes.html', context={
        'volumes': show_volume,
        'manuscripts': show_manuscripts,
    })


def thanks(request):
    return render(request, template_name='thanks.html')


def report(request):
    if request.method == 'POST':
        form = BugForm(request.POST)
        if form.is_valid():
            form.save()
            subject = 'You have a new bug report'
            to_email = form.cleaned_data['email']
            content = form.cleaned_data['name'] + '\n' + form.cleaned_data['email'] + '\n' + form.cleaned_data[
                'description']
            send_mail(
                subject,
                content,
                'anovski3@gmail.com',
                ['anovski3@gmail.com', to_email],
                fail_silently=False,
            )

            return redirect('thanks')
    else:
        form = BugForm()

    return render(request, template_name='report.html', context={'form': form})


def contact(request):
    form_class = ContactForm
    contact_form = form_class(request.POST or None)
    if request.method == 'POST':
        if contact_form.is_valid():
            contact_form.save()
            subject = 'You have a new bug report'
            to_email = contact_form.cleaned_data['email']
            content = contact_form.cleaned_data['name'] + '\n' + contact_form.cleaned_data['email'] + '\n' + \
                      contact_form.cleaned_data['content']
            print(content)
            try:
                send_mail(
                    subject,
                    content,
                    'anovski3@gmail.com',
                    ['anovski3@gmail.com', to_email],
                    fail_silently=False,
                )
            except:
                print('mail error')
            return redirect('thanks')
        else:
            contact_form = ContactForm()

    return render(request, 'contact.html', {'contact_form': contact_form})


def submit(request):
    if request.method == 'POST':
        if request.method == 'POST':
            email = request.POST['email']
            phone = request.POST['phone']
            main_author = request.POST['main_author']
            author_full_address = request.POST['author_full_address']
            title = request.POST['title']
            file = request.FILES['file']
            keywords = request.POST['keywords']

            manuscript_review = ManuscriptReview(email=email, phone=phone, main_author=main_author,
                                                 author_full_address=author_full_address, title=title, file=file,
                                                 keywords=keywords)
            manuscript_review.save()
            return redirect('thanks')
        else:
            return HttpResponse('Error saving manuscript review')

    return render(request, 'submit.html', context=None)

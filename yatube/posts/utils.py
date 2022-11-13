from django.core.paginator import Paginator


def run_pag(list_obj, request, filters):
    paginator = Paginator(list_obj, filters)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)

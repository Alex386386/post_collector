from datetime import datetime


def year(request):
    """Добавляет переменную с текущим годом."""
    # now_year = datetime.today().year
    return {'year': datetime.today().year}

from blog.utils import menu


def get_blog_context(request):
    return {'mainmenu': menu}

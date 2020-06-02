from django import template

register = template.Library()


@register.filter(name='add')
def add(value, arg):
    return value + arg


@register.filter(name='subtract')
def subtract(value, arg):
    return value - arg
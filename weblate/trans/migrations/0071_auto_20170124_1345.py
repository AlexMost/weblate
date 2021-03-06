# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-01-24 12:45
from __future__ import unicode_literals

from django.db import migrations, models
import weblate.trans.validators


class Migration(migrations.Migration):

    dependencies = [
        ('trans', '0070_auto_20161103_1412'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='subproject',
            options={'ordering': ['priority', 'project__name', 'name'], 'permissions': (('lock_subproject', 'Can lock translation for translating'), ('can_see_git_repository', 'Can see VCS repository URL'), ('view_reports', 'Can display reports')), 'verbose_name': 'Component', 'verbose_name_plural': 'Components'},
        ),
        migrations.AddField(
            model_name='subproject',
            name='priority',
            field=models.IntegerField(choices=[(60, 'Very high'), (80, 'High'), (100, 'Medium'), (120, 'Low'), (140, 'Very low')], default=100, help_text='Components with higher priority are offered first to translators.', verbose_name='Priority'),
        ),
        migrations.AlterField(
            model_name='check',
            name='check',
            field=models.CharField(choices=[('end_space', 'Trailing space'), (b'inconsistent', 'Inconsistent'), ('begin_newline', 'Starting newline'), ('max-length', 'Maximum length of translation'), ('zero-width-space', 'Zero-width space'), ('escaped_newline', 'Mismatched \\n'), ('same', 'Unchanged translation'), ('end_question', 'Trailing question'), (b'angularjs_format', 'AngularJS interpolation string'), (b'python_brace_format', 'Python brace format'), ('end_newline', 'Trailing newline'), (b'c_format', 'C format'), ('end_exclamation', 'Trailing exclamation'), ('end_ellipsis', 'Trailing ellipsis'), ('end_colon', 'Trailing colon'), ('xml-tags', 'XML tags mismatch'), (b'python_format', 'Python format'), (b'plurals', 'Missing plurals'), (b'javascript_format', 'Javascript format'), ('begin_space', 'Starting spaces'), ('bbcode', 'Mismatched BBcode'), (b'php_format', 'PHP format'), ('xml-invalid', 'Invalid XML markup'), (b'same-plurals', 'Same plurals'), ('end_stop', 'Trailing stop')], max_length=20),
        ),
        migrations.AlterField(
            model_name='subproject',
            name='filemask',
            field=models.CharField(help_text='Path of files to translate relative to repository root, use * instead of language code, for example: po/*.po or locale/*/LC_MESSAGES/django.po.', max_length=200, validators=[weblate.trans.validators.validate_filemask], verbose_name='File mask'),
        ),
    ]

# -*- coding: utf-8 -*-
#
# Copyright © 2012 - 2017 Michal Čihař <michal@cihar.com>
#
# This file is part of Weblate <https://weblate.org/>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
'''
Helper classes for management commands.
'''

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from weblate.lang.models import Language
from weblate.trans.models import Unit, SubProject, Translation


class WeblateCommand(BaseCommand):
    '''
    Command which accepts project/component/--all params to process.
    '''
    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            dest='all',
            default=False,
            help='process all components'
        )
        parser.add_argument(
            'component',
            nargs='*',
            help='Slug <project/component> of component to process'
        )

    def get_units(self, **options):
        '''
        Returns list of units matching parameters.
        '''
        if options['all']:
            return Unit.objects.all()
        return Unit.objects.filter(
            translation__subproject__in=self.get_subprojects(**options)
        )

    def iterate_units(self, **options):
        """
        Memory effective iteration over units.
        """
        units = self.get_units(**options).order_by('pk')
        count = units.count()
        if not count:
            return

        current = 0
        last = units.order_by('-pk')[0].pk
        done = 0
        step = 1000

        # Iterate over chunks
        while current < last:
            self.stdout.write(
                'Processing {0:.1f}%'.format(done * 100.0 / count),
            )
            with transaction.atomic():
                step_units = units.filter(
                    pk__gt=current
                )[:step].prefetch_related(
                    'translation__language',
                    'translation__subproject',
                    'translation__subproject__project',
                )
                for unit in step_units:
                    current = unit.pk
                    done += 1
                    yield unit
        self.stdout.write('Operation completed')

    def get_translations(self, **options):
        '''
        Returns list of translations matching parameters.
        '''
        return Translation.objects.filter(
            subproject__in=self.get_subprojects(**options)
        )

    def get_subprojects(self, **options):
        '''
        Returns list of components matching parameters.
        '''
        if options['all']:
            # all components
            result = SubProject.objects.all()
        elif len(options['component']) == 0:
            # no argumets to filter projects
            self.stderr.write(
                'Please specify either --all '
                'or at least one <project/component>'
            )
            raise CommandError('Nothing to process!')
        else:
            # start with none and add found
            result = SubProject.objects.none()

            # process arguments
            for arg in options['component']:
                # do we have also component?
                parts = arg.split('/')

                # filter by project
                found = SubProject.objects.filter(project__slug=parts[0])

                # filter by component if available
                if len(parts) == 2:
                    found = found.filter(slug=parts[1])

                # warn on no match
                if found.count() == 0:
                    self.stderr.write(
                        '"%s" did not match any components' % arg
                    )
                    raise CommandError('Nothing to process!')

                # merge results
                result |= found

        return result

    def handle(self, *args, **options):
        """
        The actual logic of the command. Subclasses must implement
        this method.

        """
        raise NotImplementedError()


class WeblateLangCommand(WeblateCommand):
    '''
    Command accepting additional language parameter to filter
    list of languages to process.
    '''
    def add_arguments(self, parser):
        super(WeblateLangCommand, self).add_arguments(parser)
        parser.add_argument(
            '--lang',
            action='store',
            dest='lang',
            default=None,
            help='Limit only to given languages (comma separated list)'
        )

    def get_units(self, **options):
        '''
        Returns list of units matching parameters.
        '''
        units = super(WeblateLangCommand, self).get_units(**options)

        if options['lang'] is not None:
            units = units.filter(
                translation__language__code=options['lang']
            )

        return units

    def get_translations(self, **options):
        '''
        Returns list of translations matching parameters.
        '''
        result = super(WeblateLangCommand, self).get_translations(
            **options
        )

        if options['lang'] is not None:
            langs = options['lang'].split(',')
            result = result.filter(language_code__in=langs)

        return result

    def handle(self, *args, **options):
        """
        The actual logic of the command. Subclasses must implement
        this method.

        """
        raise NotImplementedError()


class WeblateTranslationCommand(BaseCommand):
    """Command with target of one translation."""

    def add_arguments(self, parser):
        parser.add_argument(
            'project',
            help='Slug of project'
        )
        parser.add_argument(
            'component',
            help='Slug of component'
        )
        parser.add_argument(
            'language',
            help='Slug of language'
        )

    def get_translation(self, **options):
        """Get translation object"""
        try:
            component = SubProject.objects.get(
                project__slug=options['project'],
                slug=options['component'],
            )
        except SubProject.DoesNotExist:
            raise CommandError('No matching translation component found!')
        try:
            return Translation.objects.get(
                subproject=component,
                language__code=options['language'],
            )
        except Translation.DoesNotExist:
            if 'add' in options and options['add']:
                language = Language.objects.fuzzy_get(options['language'])
                if component.add_new_language(language, None):
                    return Translation.objects.get(
                        subproject=component,
                        language=language,
                    )
            raise CommandError('No matching translation project found!')

    def handle(self, *args, **options):
        """
        The actual logic of the command. Subclasses must implement
        this method.

        """
        raise NotImplementedError()

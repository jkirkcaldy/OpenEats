#!/usr/bin/env python
# encoding: utf-8
from __future__ import unicode_literals

import uuid
import tempfile
import requests
from django.core import files
from django.db.models import Count
from v1.recipe_groups.models import Cuisine, Course
from rest_framework import permissions, viewsets, filters
from rest_framework.response import Response
import random
from . import serializers
from .models import Recipe
from v1.common.permissions import IsOwnerOrReadOnly
from v1.common.recipe_search import get_search_results


class RecipeViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """
    queryset = Recipe.objects.all()
    serializer_class = serializers.RecipeSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    filter_backends = (filters.DjangoFilterBackend, filters.SearchFilter)
    filter_fields = ('course__slug', 'cuisine__slug', 'course', 'cuisine', 'title', 'rating')
    search_fields = ('title', 'tags__title', 'ingredient_groups__ingredients__title')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        url = request.data.get('image')
        if url:
            # Steam the image from the url
            request_image = requests.get(url, stream=True)

            # Create a temporary file
            lf = tempfile.NamedTemporaryFile()

            # Read the streamed image in sections
            for block in request_image.iter_content(1024 * 8):

                # If no more file then stop
                if not block:
                    break

                # Write image block to temporary file
                lf.write(block)

            # Get the recently created recipe and add the image
            recipe = Recipe.objects.get(pk=serializer.data['id'])
            recipe.photo.save(str(uuid.uuid4()), files.File(lf))
            recipe.save()

        return Response(serializer.data)


class MiniBrowseViewSet(viewsets.mixins.ListModelMixin,
                        viewsets.GenericViewSet):
    """
    This viewset automatically provides `list` action.
    """
    queryset = Recipe.objects.all()
    serializer_class = serializers.MiniBrowseSerializer

    def list(self, request, *args, **kwargs):
        # Get the limit from the request and the count from the DB.
        # Compare to make sure you aren't accessing more than possible.
        limit = int(request.query_params.get('limit'))
        count = Recipe.objects.count()
        if limit > count:
            limit = count

        # Get all ids from the DB.
        my_ids = Recipe.objects.values_list('id', flat=True)
        # Select a random sample from the DB.
        rand_ids = random.sample(my_ids, limit)
        # set teh queryset to that random sample.
        self.queryset = Recipe.objects.filter(id__in=rand_ids)

        return super(MiniBrowseViewSet, self).list(request, *args, **kwargs)


class RatingViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = serializers.RatingSerializer

    def get_queryset(self):
        query = Recipe.objects

        filter_set = {}
        if 'cuisine' in self.request.query_params:
            try:
                filter_set['cuisine'] = Cuisine.objects.get(
                    slug=self.request.query_params.get('cuisine')
                )
            except:
                return []

        if 'course' in self.request.query_params:
            try:
                filter_set['course'] = Course.objects.get(
                    slug=self.request.query_params.get('course')
                )
            except:
                return []

        if 'search' in self.request.query_params:
            query = get_search_results(
                ['title', 'ingredient_groups__ingredients__title', 'tags__title'],
                query,
                self.request.query_params.get('search')
            ).distinct()

        query = query.filter(**filter_set)

        return query.values('rating').annotate(total=Count('id', distinct=True)).order_by('-rating')

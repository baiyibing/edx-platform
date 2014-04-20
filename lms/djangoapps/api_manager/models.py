# pylint: disable=E1101

""" Database ORM models managed by this Django app """

from django.contrib.auth.models import Group
from django.db import models
from django.utils import timezone


class GroupRelationship(models.Model):
    """
    The GroupRelationship model contains information describing the relationships of a group,
    which allows us to utilize Django's user/group/permission
    models and features instead of rolling our own.
    """
    group = models.OneToOneField(Group, primary_key=True)
    name = models.CharField(max_length=255)
    parent_group = models.ForeignKey('self',
                                     related_name="child_groups",
                                     blank=True, null=True, default=0)
    linked_groups = models.ManyToManyField('self',
                                           through="LinkedGroupRelationship",
                                           symmetrical=False,
                                           related_name="linked_to+"),
    record_active = models.BooleanField(default=True)
    record_date_created = models.DateTimeField(default=timezone.now())
    record_date_modified = models.DateTimeField(auto_now=True)

    def add_linked_group_relationship(self, to_group_relationship, symmetrical=True):
        """ Create a new group-group relationship """
        relationship = LinkedGroupRelationship.objects.get_or_create(
            from_group_relationship=self,
            to_group_relationship=to_group_relationship)
        if symmetrical:
            # avoid recursion by passing `symm=False`
            to_group_relationship.add_linked_group_relationship(self, False)
        return relationship

    def remove_linked_group_relationship(self, to_group_relationship, symmetrical=True):
        """ Remove an existing group-group relationship """
        LinkedGroupRelationship.objects.filter(
            from_group_relationship=self,
            to_group_relationship=to_group_relationship).delete()
        if symmetrical:
            # avoid recursion by passing `symm=False`
            to_group_relationship.remove_linked_group_relationship(self, False)
        return

    def get_linked_group_relationships(self):
        """ Retrieve an existing group-group relationship """
        efferent_relationships = LinkedGroupRelationship.objects.filter(from_group_relationship=self)
        matching_relationships = efferent_relationships
        return matching_relationships

    def check_linked_group_relationship(self, relationship_to_check, symmetrical=False):
        """ Confirm the existence of a possibly-existing group-group relationship """
        query = dict(
            to_group_relationships__from_group_relationship=self,
            to_group_relationships__to_group_relationship=relationship_to_check,
        )
        if symmetrical:
            query.update(
                from_group_relationships__to_group_relationship=self,
                from_group_relationships__from_group_relationship=relationship_to_check,
            )
        return GroupRelationship.objects.filter(**query).exists()


class LinkedGroupRelationship(models.Model):
    """
    The LinkedGroupRelationship model manages self-referential two-way
    relationships between group entities via the GroupRelationship model.
    Specifying the intermediary table allows for the definition of additional
    relationship information
    """
    from_group_relationship = models.ForeignKey(GroupRelationship,
                                                related_name="from_group_relationships",
                                                verbose_name="From Group")
    to_group_relationship = models.ForeignKey(GroupRelationship,
                                              related_name="to_group_relationships",
                                              verbose_name="To Group")
    record_active = models.BooleanField(default=True)
    record_date_created = models.DateTimeField(default=timezone.now())
    record_date_modified = models.DateTimeField(auto_now=True)


class CourseGroupRelationship(models.Model):
    """
    The CourseGroupRelationship model contains information describing the
    link between a course and a group.  A typical use case for this table
    is to manage the courses for an XSeries or other sort of program.
    """
    course_id = models.CharField(max_length=255, db_index=True)
    group = models.ForeignKey(Group, db_index=True)

from datetime import datetime
from django.db import models
from django.contrib.auth.models import User


class Cluster(models.Model):
    identifier = models.CharField(max_length=100)
    size = models.IntegerField()
    public_key = models.CharField(max_length=100000)
    creation_date = models.DateField(blank=True, null=True)
    created_by = models.ForeignKey(User, related_name='cluster_created_by')

    def __str__(self):
        return "<Cluster {}>".format(self.identifier)

    def __repr__(self):
        return "<Cluster {} {}>".format(self.identifier, self.size)

    def save(self):
        self.creation_date = datetime.now()
        super(Cluster, self).save()


class Worker(models.Model):
    identifier = models.CharField(max_length=100)
    public_key = models.CharField(max_length=100000)
    creation_date = models.DateField(blank=True, null=True)
    created_by = models.ForeignKey(User, related_name='worker_created_by')

    def __str__(self):
        return "<Worker {}>".format(self.identifier)

    def __repr__(self):
        return "<Worker {}>".format(self.identifier)

    def save(self):
        self.creation_date = datetime.now()
        super(Cluster, self).save()

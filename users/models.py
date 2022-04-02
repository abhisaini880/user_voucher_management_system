from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser


class UserManager(BaseUserManager):
    def create_user(self, name, mobile_number, password=None):
        """
        Creates and saves a User with the given mobile number and password.
        """
        if not name:
            raise ValueError("Users must have a name")

        if not mobile_number:
            raise ValueError("Users must have an mobile_number")

        user = self.model(mobile_number=mobile_number, name=name)

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_staffuser(self, name, mobile_number, password):
        """
        Creates and saves a staff user with the given mobile_number and password.
        """
        user = self.create_user(
            name,
            mobile_number,
            password=password,
        )
        user.staff = True
        user.save(using=self._db)
        return user

    def create_superuser(self, name, mobile_number, password):
        """
        Creates and saves a superuser with the given mobile_number and password.
        """
        user = self.create_user(
            name,
            mobile_number,
            password=password,
        )
        user.staff = True
        user.admin = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    mobile_number = models.BigIntegerField(unique=True)
    name = models.CharField(max_length=100, null=False)
    is_active = models.BooleanField(default=True)
    staff = models.BooleanField(default=False)  # a admin user; non super-user
    admin = models.BooleanField(default=False)  # a superuser

    USERNAME_FIELD = "mobile_number"
    REQUIRED_FIELDS = ["name"]  # Email & Password are required by default.
    objects = UserManager()

    def __str__(self):
        return f"{self.name} - {self.mobile_number}"

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        return self.staff

    @property
    def is_admin(self):
        "Is the user a admin member?"
        return self.admin

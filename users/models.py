from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser


class UserManager(BaseUserManager):
    def create_user(
        self,
        name,
        mobile_number,
        unique_id=None,
        ws_name=None,
        region=None,
        points_earned=0,
        password=None,
        admin=False,
    ):
        """
        Creates and saves a User with the given mobile number and password.
        """
        if not name:
            raise ValueError("Users must have a name")

        if not mobile_number:
            raise ValueError("Users must have an mobile_number")

        user = self.model(
            mobile_number=mobile_number,
            ws_name=ws_name,
            unique_id=unique_id,
            name=name,
            region=region,
            points_earned=points_earned,
        )
        if admin:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_staffuser(self, name, mobile_number, password):
        """
        Creates and saves a staff user with the given mobile_number and password.
        """
        user = self.create_user(
            name, mobile_number, password=password, admin=True
        )
        user.staff = True
        user.save(using=self._db)
        return user

    def create_superuser(self, name, mobile_number, password, region):
        """
        Creates and saves a superuser with the given mobile_number and password.
        """
        user = self.create_user(
            name, mobile_number, password=password, region=region, admin=True
        )
        user.staff = True
        user.admin = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    mobile_number = models.BigIntegerField(unique=True)
    unique_id = models.CharField(max_length=100, unique=True, null=True)
    ws_name = models.CharField(max_length=100, null=True)
    name = models.CharField(max_length=100, null=True)
    region = models.CharField(max_length=100, null=True)
    points_earned = models.IntegerField(default=0)
    points_redeemed = models.IntegerField(default=0)
    current_points = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    otp = models.CharField(max_length=4, null=True)
    login_retry = models.IntegerField(default=0)
    read_only = models.BooleanField(default=True)
    voucher_write = models.BooleanField(default=False)
    staff = models.BooleanField(default=False)  # a admin user; non super-user
    staff_editor = models.BooleanField(
        default=False
    )  # a admin user; non super-user with write access
    admin = models.BooleanField(default=False)  # a superuser

    USERNAME_FIELD = "mobile_number"
    REQUIRED_FIELDS = [
        "name",
        "region",
    ]  # Email & Password are required by default.
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
    def points(self):
        "return current points"
        return self.current_points

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        return self.staff

    @property
    def is_admin(self):
        "Is the user a admin member?"
        return self.admin

    class Meta:
        db_table = "users"

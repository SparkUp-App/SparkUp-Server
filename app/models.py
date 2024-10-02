import uuid
from enum import Enum as PyEnum
from collections import OrderedDict

from flask_security import SQLAlchemyUserDatastore, UserMixin, RoleMixin, AsaList

from sqlalchemy import PickleType, Enum as SQLEnum
from sqlalchemy.ext.mutable import MutableList

from app.extensions import db


# Auth Models
class RolesUsers(db.Model):
    __tablename__ = 'roles_users'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column('user_id', db.Integer(), db.ForeignKey('users.id'))
    role_id = db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))


class Role(db.Model, RoleMixin):
    __tablename__ = 'role'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))
    permissions = db.Column(MutableList.as_mutable(AsaList()), nullable=True)


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean, default=False, nullable=False)
    fs_uniquifier = db.Column(db.String(64), unique=True, nullable=False)
    roles = db.relationship(
        'Role',
        secondary='roles_users',
        backref=db.backref('users', lazy='dynamic')
    )

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if not self.fs_uniquifier:
            self.fs_uniquifier = str(uuid.uuid4())


user_datastore = SQLAlchemyUserDatastore(db, User, None)


# Profile Models
class EducationLevelEnum(PyEnum):
    NO_FORMAL_EDUCATION = 'No Formal Education'
    PRIMARY_SCHOOL = 'Primary School'
    SECONDARY_SCHOOL = 'Secondary School'
    UNDERGRAD = 'Undergraduate'
    POSTGRAD = 'Postgraduate'
    PHD = 'PhD'
    PREFER_NOT_TO_SAY = 'Prefer not to say'


class MBTIEnum(PyEnum):
    INTJ = 'INTJ'
    INTP = 'INTP'
    ENTJ = 'ENTJ'
    ENTP = 'ENTP'
    INFJ = 'INFJ'
    INFP = 'INFP'
    ENFJ = 'ENFJ'
    ENFP = 'ENFP'
    ISTJ = 'ISTJ'
    ISFJ = 'ISFJ'
    ESTJ = 'ESTJ'
    ESFJ = 'ESFJ'
    ISTP = 'ISTP'
    ISFP = 'ISFP'
    ESTP = 'ESTP'
    ESFP = 'ESFP'
    PREFER_NOT_TO_SAY = 'Prefer not to say'


class ConstellationEnum(PyEnum):
    ARIES = 'Aries'
    TAURUS = 'Taurus'
    GEMINI = 'Gemini'
    CANCER = 'Cancer'
    LEO = 'Leo'
    VIRGO = 'Virgo'
    LIBRA = 'Libra'
    SCORPIO = 'Scorpio'
    SAGITTARIUS = 'Sagittarius'
    CAPRICORN = 'Capricorn'
    AQUARIUS = 'Aquarius'
    PISCES = 'Pisces'
    PREFER_NOT_TO_SAY = 'Prefer not to say'


class BloodTypeEnum(PyEnum):
    A = 'A'
    B = 'B'
    AB = 'AB'
    O = 'O'
    OTHER = 'Other'
    PREFER_NOT_TO_SAY = 'Prefer not to say'


class ReligionEnum(PyEnum):
    AGNOSTIC = 'Agnostic'
    ATHEIST = 'Atheist'
    BUDDHIST = 'Buddhist'
    CATHOLIC = 'Catholic'
    CHRISTIAN = 'Christian'
    HINDU = 'Hindu'
    JEWISH = 'Jewish'
    MUSLIM = 'Muslim'
    SIKH = 'Sikh'
    SPIRITUAL = 'Spiritual'
    ORTHODOX_CHRISTIAN = 'Orthodox Christian'
    PROTESTANT = 'Protestant'
    SHINTO = 'Shinto'
    TAOIST = 'Taoist'
    OTHER = 'Other'
    PREFER_NOT_TO_SAY = 'Prefer not to say'

class SexualityEnum(PyEnum):
    STRAIGHT = 'Straight'
    GAY = 'Gay'
    LESBIAN = 'Lesbian'
    BISEXUAL = 'Bisexual'
    ASEXUAL = 'Asexual'
    PANSEXUAL = 'Pansexual'
    QUEER = 'Queer'
    QUESTIONING = 'Questioning'
    NOT_LISTED = 'Not listed'
    PREFER_NOT_TO_SAY = 'Prefer not to say'


class EthnicityEnum(PyEnum):
    BLACK_AFRICAN_DESCENT = 'Black/African Descent'
    EAST_ASIAN = 'East Asian'
    SOUTH_ASIAN = 'South Asian'
    SOUTHEAST_ASIAN = 'Southeast Asian'
    HISPANIC_LATINO = 'Hispanic/Latino'
    MIDDLE_EASTERN_NORTH_AFRICAN = 'Middle Eastern/North African'
    NATIVE_AMERICAN_INDIGENOUS = 'Native American/Indigenous'
    PACIFIC_ISLANDER = 'Pacific Islander'
    WHITE_CAUCASIAN = 'White/Caucasian'
    MULTIRACIAL = 'Multiracial'
    OTHER = 'Other'
    PREFER_NOT_TO_SAY = 'Prefer not to say'


class DietEnum(PyEnum):
    OMNIVORE = 'Omnivore'
    VEGETARIAN = 'Vegetarian'
    VEGAN = 'Vegan'
    PESCATARIAN = 'Pescatarian'
    KETOGENIC = 'Ketogenic'
    PALEO = 'Paleo'
    OTHER = 'Other'
    PREFER_NOT_TO_SAY = 'Prefer not to say'


class Profile(db.Model):
    __tablename__ = 'profiles'
    id = db.Column(db.Integer,
                   db.ForeignKey('users.id', ondelete='CASCADE'),
                   primary_key=True)
    phone = db.Column(db.String(20), nullable=False)
    nickname = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    gender = db.Column(db.Integer, nullable=False)
    bio = db.Column(db.Text)
    current_location = db.Column(db.Text)
    hometown = db.Column(db.Text)
    college = db.Column(db.Text)
    job_title = db.Column(db.Text)
    education_level = db.Column(SQLEnum(EducationLevelEnum))
    mbti = db.Column(SQLEnum(MBTIEnum))
    constellation = db.Column(SQLEnum(ConstellationEnum))
    blood_type = db.Column(SQLEnum(BloodTypeEnum))
    religion = db.Column(SQLEnum(ReligionEnum))
    sexuality = db.Column(SQLEnum(SexualityEnum))
    ethnicity = db.Column(SQLEnum(EthnicityEnum))
    diet = db.Column(SQLEnum(DietEnum))
    smoke = db.Column(db.Integer)
    drinking = db.Column(db.Integer)
    marijuana = db.Column(db.Integer)
    drugs = db.Column(db.Integer)
    skills = db.Column(MutableList.as_mutable(PickleType), default=lambda: [])
    personalities = db.Column(MutableList.as_mutable(PickleType), default=lambda: [])
    languages = db.Column(MutableList.as_mutable(PickleType), default=lambda: [])
    interest_types = db.Column(MutableList.as_mutable(PickleType), default=lambda: [])

    def serialize(self):
        return OrderedDict([
            ('id', self.id),
            ('phone', self.phone),
            ('nickname', self.nickname),
            ('dob', self.dob.isoformat() if self.dob else None),  # Convert date to ISO format
            ('gender', self.gender),
            ('bio', self.bio),
            ('current_location', self.current_location),
            ('hometown', self.hometown),
            ('college', self.college),
            ('job_title', self.job_title),
            ('education_level', self.education_level.name if self.education_level else None),
            ('mbti', self.mbti.name if self.mbti else None),
            ('constellation', self.constellation.name if self.constellation else None),
            ('blood_type', self.blood_type.name if self.blood_type else None),
            ('religion', self.religion.name if self.religion else None),
            ('sexuality', self.sexuality.name if self.sexuality else None),
            ('ethnicity', self.ethnicity.name if self.ethnicity else None),
            ('diet', self.diet.name if self.diet else None),
            ('smoke', self.smoke),
            ('drinking', self.drinking),
            ('marijuana', self.marijuana),
            ('drugs', self.drugs),
            ('skills', self.skills),
            ('personalities', self.personalities),
            ('languages', self.languages),
            ('interest_types', self.interest_types)
        ])

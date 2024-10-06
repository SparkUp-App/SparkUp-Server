import uuid
from enum import Enum as PyEnum
from collections import OrderedDict
from datetime import datetime, timezone

from flask_security import SQLAlchemyUserDatastore, UserMixin, RoleMixin, AsaList
from flask_restx import fields

from sqlalchemy import select, exists, PickleType, Enum as SQLEnum
from sqlalchemy.ext.mutable import MutableList, MutableDict

from app.extensions import db


# General
class DictItem(fields.Raw):
    def output(self, key, obj, *args, **kwargs):
        try:
            dct = getattr(obj, self.attribute)
        except AttributeError:
            return {}
        return dct or {}


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

    profile = db.relationship(
        'Profile',
        back_populates='user',
        uselist=False,
        cascade='all, delete-orphan',
        foreign_keys='Profile.id',
    )

    posts = db.relationship('Post',
                            back_populates='user',
                            lazy='select',
                            cascade='all, delete-orphan')

    liked_comments = db.relationship(
        'PostCommentLike',
        back_populates='user',
        lazy='dynamic',
        cascade='all, delete-orphan',
    )

    liked_posts = db.relationship('PostLike',
                                  back_populates='user',
                                  lazy='dynamic',
                                  cascade='all, delete-orphan')

    comments = db.relationship('PostComment',
                               back_populates='user',
                               lazy='dynamic',
                               cascade='all, delete-orphan')

    applied_posts = db.relationship('PostApplicant', back_populates='user')

    bookmarked_posts = db.relationship(
        'PostBookmark',
        back_populates='user',
        lazy='select',
        cascade='all, delete-orphan',
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

    user = db.relationship("User", back_populates="profile")

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
            ('education_level', self.education_level.value if self.education_level else None),
            ('mbti', self.mbti.value if self.mbti else None),
            ('constellation', self.constellation.value if self.constellation else None),
            ('blood_type', self.blood_type.value if self.blood_type else None),
            ('religion', self.religion.value if self.religion else None),
            ('sexuality', self.sexuality.value if self.sexuality else None),
            ('ethnicity', self.ethnicity.value if self.ethnicity else None),
            ('diet', self.diet.value if self.diet else None),
            ('smoke', self.smoke),
            ('drinking', self.drinking),
            ('marijuana', self.marijuana),
            ('drugs', self.drugs),
            ('skills', self.skills),
            ('personalities', self.personalities),
            ('languages', self.languages),
            ('interest_types', self.interest_types)
        ])


# Post Models
class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type = db.Column(db.String(50))
    user_id = db.Column(db.Integer,
                        db.ForeignKey('users.id', ondelete='CASCADE'),
                        nullable=False)

    post_created_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    post_last_updated_date = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    title = db.Column(db.Text, nullable=False)
    content = db.Column(db.UnicodeText, nullable=False)
    event_start_date = db.Column(db.DateTime, nullable=False)
    event_end_date = db.Column(db.DateTime, nullable=False)
    number_of_people_required = db.Column(db.Integer, nullable=False)
    location = db.Column(db.Text, nullable=False)
    skills = db.Column(MutableList.as_mutable(PickleType), default=lambda: [])
    personalities = db.Column(MutableList.as_mutable(PickleType), default=lambda: [])
    languages = db.Column(MutableList.as_mutable(PickleType), default=lambda: [])
    attributes = db.Column(MutableDict.as_mutable(PickleType), default=lambda: {})
    likes = db.relationship('PostLike',
                            back_populates='post',
                            lazy=True,
                            cascade='all, delete-orphan')

    user = db.relationship('User', back_populates='posts')

    comments = db.relationship('PostComment',
                               back_populates='post',
                               lazy=True,
                               cascade='all, delete-orphan')

    applicants = db.relationship('PostApplicant', back_populates='post', cascade='all, delete-orphan')

    bookmarks = db.relationship('PostBookmark',
                                back_populates='post',
                                lazy=True,
                                cascade='all, delete-orphan')

    def serialize(self, user_id, simple=False):
        post_dict = OrderedDict([('id', self.id),
                            ('nickname', self.user.profile.nickname),
                            ('type', self.type),
                            ('title', self.title),
                            ('content', self.content),
                            ('event_start_date', self.event_start_date.strftime('%Y-%m-%d %H:%M:%S')),
                            ('event_end_date', self.event_end_date.strftime('%Y-%m-%d %H:%M:%S')),
                            ('number_of_people_required', self.number_of_people_required),
                            ('likes', len(self.likes)),
                            ('liked', any(like.user_id == user_id for like in self.likes)),
                            ('bookmarks', len(self.bookmarks)),
                            ('bookmarked', any(bookmark.user_id == user_id for bookmark in self.bookmarks)),
                            ('comments', len(self.comments)),
                            ('applicants', len(self.applicants)),])
        if not simple:
            post_dict['location'] = self.location,
            post_dict['skills'] = self.skills,
            post_dict['personalities'] = self.personalities,
            post_dict['languages'] = self.languages,
            post_dict['attributes'] = self.attributes
        application = PostApplicant.query.get((user_id, self.id))
        if application:
            post_dict['application_status'] = application.review_status
        return post_dict

    def manual_update(self):
        self.post_last_updated_date = datetime.now(timezone.utc)


class PostLike(db.Model):
    __tablename__ = 'post_likes'
    user_id = db.Column(db.Integer,
                        db.ForeignKey('users.id', ondelete='CASCADE'),
                        primary_key=True)
    post_id = db.Column(db.Integer,
                        db.ForeignKey('posts.id', ondelete='CASCADE'),
                        primary_key=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    user = db.relationship('User', back_populates='liked_posts')
    post = db.relationship('Post', back_populates='likes')


class PostBookmark(db.Model):
    __tablename__ = 'post_bookmarks'
    user_id = db.Column(db.Integer,
                        db.ForeignKey('users.id', ondelete='CASCADE'),
                        primary_key=True)
    post_id = db.Column(db.Integer,
                        db.ForeignKey('posts.id', ondelete='CASCADE'),
                        primary_key=True)
    created_at = db.Column(db.DateTime,
                           default=lambda: datetime.now(timezone.utc))
    user = db.relationship('User', back_populates='bookmarked_posts')
    post = db.relationship('Post', back_populates='bookmarks')


class PostApplicant(db.Model):
    __tablename__ = 'post_applicants'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id', ondelete='CASCADE'), primary_key=True)
    content = db.Column(db.UnicodeText, default='', nullable=False)
    applied_time = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    review_status = db.Column(db.Integer, default=0, nullable=False)  # 0: still reviewing, 1: rejected, 2: matched

    post = db.relationship('Post', back_populates='applicants')
    user = db.relationship('User', back_populates='applied_posts')


class PostComment(db.Model):
    __tablename__ = 'post_comments'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer,
                        db.ForeignKey('users.id', ondelete='CASCADE'),
                        nullable=True)
    post_id = db.Column(db.Integer,
                        db.ForeignKey('posts.id', ondelete='CASCADE'),
                        nullable=False)
    content = db.Column(db.UnicodeText, nullable=False)
    deleted = db.Column(db.Boolean, default=False, nullable=False)
    comment_created_date = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False)
    comment_last_updated_date = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    floor = db.Column(db.Integer, nullable=False)
    likes = db.relationship('PostCommentLike',
                            back_populates='comment',
                            lazy=True,
                            cascade='all, delete-orphan')

    post = db.relationship('Post', back_populates='comments')
    user = db.relationship('User', back_populates='comments')

    def serialize(self, user_id):
        comment_dict = OrderedDict([
            ('id', self.id),
            ('post_id', self.post_id),
            ('user_id', self.user_id),
            ('content', self.content),
            ('deleted', self.deleted),
            ('comment_created_date', self.comment_created_date.strftime('%Y-%m-%d %H:%M:%S')),
            ('comment_last_updated_date', self.comment_last_updated_date.strftime('%Y-%m-%d %H:%M:%S')),
            ('floor', self.floor),
            ('likes', len(self.likes)),
        ])
        if self.user:
            comment_dict['nickname'] = Profile.query.get(self.user_id).nickname
            comment_dict['liked'] = db.session.execute(
                select(exists().where(
                    PostCommentLike.user_id == user_id,
                    PostCommentLike.comment_id == self.id
                ))
            ).scalar()
        return comment_dict


class PostCommentLike(db.Model):
    __tablename__ = 'post_comment_likes'
    user_id = db.Column(db.Integer,
                        db.ForeignKey('users.id', ondelete='CASCADE'),
                        primary_key=True)
    comment_id = db.Column(db.Integer,
                           db.ForeignKey('post_comments.id', ondelete='CASCADE'),
                           primary_key=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    user = db.relationship('User', back_populates='liked_comments')
    comment = db.relationship('PostComment', back_populates='likes')

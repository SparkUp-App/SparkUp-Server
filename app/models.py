import uuid
from enum import Enum as PyEnum
from collections import OrderedDict
from datetime import datetime, timezone

from flask_security import SQLAlchemyUserDatastore, UserMixin, RoleMixin, AsaList
from flask_restx import fields

from sqlalchemy import select, exists, PickleType, Enum as SQLEnum
from sqlalchemy.ext.mutable import MutableList, MutableDict

from app.extensions import db
from app.utils import to_iso8601


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
                            lazy='dynamic',
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

    bookmarked_posts = db.relationship(
        'PostBookmark',
        back_populates='user',
        lazy='select',
        cascade='all, delete-orphan',
    )

    applied_posts = db.relationship('PostApplicant', back_populates='user')

    chat_rooms = db.relationship(
        'ChatRoomUser',
        back_populates='user',
        lazy='dynamic',
        cascade='all, delete-orphan',
    )

    rating = db.Column(db.Float, default=0.0)
    ratings = db.relationship('Reference',
                              foreign_keys='Reference.to_user_id',
                              backref='to_user',
                              lazy='dynamic',
                              cascade="all, delete-orphan")

    given_ratings = db.relationship('Reference',
                                    foreign_keys='Reference.from_user_id',
                                    backref='from_user',
                                    lazy='dynamic',
                                    cascade="all, delete-orphan")

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
    dob = db.Column(db.DateTime, nullable=False)
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
            ('dob', to_iso8601(self.dob) if self.dob else None),  # Convert date to ISO format
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

    chat_room = db.relationship('ChatRoom',
                                uselist=False,
                                back_populates='post')

    references = db.relationship('Reference',
                                 back_populates='post',
                                 cascade='all, delete-orphan')

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
    attributes = db.Column(MutableDict.as_mutable(PickleType), default=lambda: {}, nullable=True)

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
            ('comment_created_date', to_iso8601(self.comment_created_date)),
            ('comment_last_updated_date', to_iso8601(self.comment_last_updated_date)),
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


class ChatRoom(db.Model):
    __tablename__ = 'chat_rooms'
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id', ondelete='CASCADE'), primary_key=True)
    post = db.relationship('Post', back_populates='chat_room', lazy='joined')
    name = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    messages = db.relationship('Message',
                               back_populates='room',
                               lazy='dynamic',
                               cascade='all, delete-orphan')
    users = db.relationship('ChatRoomUser',
                            back_populates='room',
                            lazy='dynamic',
                            cascade='all, delete-orphan')


class ChatRoomUser(db.Model):
    __tablename__ = 'chat_room_users'
    __table_args__ = (db.UniqueConstraint('post_id', 'user_id', name='_chat_room_user_uc'),)
    post_id = db.Column(db.Integer, db.ForeignKey('chat_rooms.post_id', ondelete='CASCADE'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    joined_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    user = db.relationship('User', back_populates='chat_rooms')
    room = db.relationship('ChatRoom', back_populates='users')


class Message(db.Model):
    __tablename__ = 'messages'
    __table_args__ = (
        db.Index('idx_messages_post_id', 'post_id'),  # Simple index on post_id is sufficient
    )
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer,
                        db.ForeignKey('chat_rooms.post_id', ondelete='CASCADE'),
                        nullable=False)
    sender_id = db.Column(db.Integer,
                          db.ForeignKey('users.id', ondelete='CASCADE'),
                          nullable=False)
    content = db.Column(db.UnicodeText, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    read_users = db.Column(MutableList.as_mutable(PickleType), default=lambda: [])

    room = db.relationship('ChatRoom', back_populates='messages')


class Reference(db.Model):
    __tablename__ = 'references'
    from_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    to_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id', ondelete='CASCADE'), primary_key=True)
    rating = db.Column(db.Integer, nullable=False)
    content = db.Column(db.UnicodeText, nullable=False)

    post = db.relationship('Post', back_populates='references')
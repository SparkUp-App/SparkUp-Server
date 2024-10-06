from datetime import datetime

from flask import Blueprint, request, jsonify, current_app
from flask_restx import Api, Namespace, Resource, fields

from app.utils import jsonify_response
from app.extensions import db
from app.models import (EducationLevelEnum, MBTIEnum, ConstellationEnum, BloodTypeEnum,
                        ReligionEnum, SexualityEnum, EthnicityEnum, DietEnum, User, Profile)

profile_bp = Blueprint('profile_bp', __name__)
profile_api = Api(
    profile_bp,
    version='1.0',
    title='Profile API',
    description='Profile API',
    doc='/docs',
)
profile_ns = profile_api.namespace('', description='Profile operations')

# Models
profile_model = profile_ns.model(
    'Profile',
    {
        'phone': fields.String(required=True, description='Phone number'),
        'nickname': fields.String(required=True, description='Nickname'),
        'dob': fields.Date(required=True, description='Date of birth in ISO format'),
        'gender': fields.Integer(
            required=True,
            description='Gender (0: Male, 1: Female, 2: Non-Binary, 3: Prefer not to say)'
        ),
        'bio': fields.String(description='Bio'),
        'current_location': fields.String(description='Current location'),
        'hometown': fields.String(description='Hometown'),
        'college': fields.String(description='College'),
        'job_title': fields.String(description='Job title'),
        'education_level': fields.String(
            description='Education level',
            enum=[e.value for e in EducationLevelEnum]
        ),
        'mbti': fields.String(
            description='MBTI personality type',
            enum=[e.value for e in MBTIEnum]
        ),
        'constellation': fields.String(
            description='Astrological sign',
            enum=[e.value for e in ConstellationEnum]
        ),
        'blood_type': fields.String(
            description='Blood type',
            enum=[e.value for e in BloodTypeEnum]
        ),
        'religion': fields.String(
            description='Religion',
            enum=[e.value for e in ReligionEnum]
        ),
        'sexuality': fields.String(
            description='Sexuality',
            enum=[e.value for e in SexualityEnum]
        ),
        'ethnicity': fields.String(
            description='Ethnicity',
            enum=[e.value for e in EthnicityEnum]
        ),
        'diet': fields.String(
            description='Diet preferences',
            enum=[e.value for e in DietEnum]
        ),
        'smoke': fields.Integer(
            default=0,
            description='Smoking habits (0: No, 1: Yes, 2: Occasionally, 3: Prefer not to say)',
        ),
        'drinking': fields.Integer(
            default=0,
            description='Drinking habits (0: No, 1: Yes, 2: Occasionally, 3: Prefer not to say)',
        ),
        'marijuana': fields.Integer(
            default=0,
            description='Marijuana usage (0: No, 1: Yes, 2: Occasionally, 3: Prefer not to say)',
        ),
        'drugs': fields.Integer(
            default=0,
            description='Other drugs usage (0: No, 1: Yes, 2: Occasionally, 3: Prefer not to say)',
        ),
        'skills': fields.List(
            fields.String,
            description='Skills of the user'
        ),
        'personalities': fields.List(
            fields.String,
            description='Personalities of the user'
        ),
        'languages': fields.List(
            fields.String,
            description='Languages spoken by the user'
        ),
        'interest_types': fields.List(
            fields.String,
            description='Interested event type of the user'
        ),
    }
)


# Routes
@profile_ns.route('/update/<int:user_id>')
class ProfileUpdate(Resource):
    @profile_ns.expect(profile_model)
    @profile_ns.response(201, 'Profile create/update successfully.')
    @profile_ns.response(400, 'Validation Error')
    @profile_ns.response(404, 'User not found')
    def post(self, user_id):
        data = request.get_json()

        current_app.logger.info(f"Received request to update profile for user_id: {user_id}")

        # Check if user exist
        user = User.query.get(user_id)
        if not user:
            current_app.logger.error(f"User not found for user_id: {user_id}")
            profile_ns.abort(404, 'User not found')

        # Check required fields
        required_fields = ['phone', 'nickname', 'dob', 'gender']
        for field in required_fields:
            if field not in data:
                current_app.logger.error(f"Missing required field: {field}")
                profile_ns.abort(400, f'Missing required field: {field}')

        # Check dob
        try:
            dob_date = datetime.strptime(data['dob'], '%Y-%m-%d').date()
        except ValueError:
            current_app.logger.error(f"Invalid date for dob: {data['dob']}")
            profile_ns.abort(400, f'Invalid date for dob: {data["dob"]}, use YYY-MM-DD format')

        # Check enums
        if 'education_level' in data and data['education_level'] is not None:
            data['education_level'] = EducationLevelEnum(data['education_level'])
        else:
            data['education_level'] = EducationLevelEnum.PREFER_NOT_TO_SAY
        if 'mbti' in data and data['mbti'] is not None:
            data['mbti'] = MBTIEnum(data['mbti'])
        else:
            data['mbti'] = MBTIEnum.PREFER_NOT_TO_SAY
        if 'constellation' in data and data['constellation'] is not None:
            data['constellation'] = ConstellationEnum(data['constellation'])
        else:
            data['constellation'] = ConstellationEnum.PREFER_NOT_TO_SAY
        if 'blood_type' in data and data['blood_type'] is not None:
            data['blood_type'] = BloodTypeEnum(data['blood_type'])
        else:
            data['blood_type'] = BloodTypeEnum.PREFER_NOT_TO_SAY
        if 'religion' in data and data['religion'] is not None:
            data['religion'] = ReligionEnum(data['religion'])
        else:
            data['religion'] = ReligionEnum.PREFER_NOT_TO_SAY
        if 'sexuality' in data and data['sexuality'] is not None:
            data['sexuality'] = SexualityEnum(data['sexuality'])
        else:
            data['sexuality'] = SexualityEnum.PREFER_NOT_TO_SAY
        if 'ethnicity' in data and data['ethnicity'] is not None:
            data['ethnicity'] = EthnicityEnum(data['ethnicity'])
        else:
            data['ethnicity'] = EthnicityEnum.PREFER_NOT_TO_SAY
        if 'diet' in data and data['diet'] is not None:
            data['diet'] = DietEnum(data['diet'])
        else:
            data['diet'] = DietEnum.PREFER_NOT_TO_SAY

        # Create or Update the Profile
        profile = Profile.query.get(user_id)
        create_profile = profile is None
        if create_profile:
            profile = Profile(id=user_id)

        profile.phone = data['phone']
        profile.nickname = data['nickname']
        profile.dob = dob_date
        profile.gender = data['gender']
        profile.bio = data.get('bio', '')
        profile.current_location = data.get('current_location', '')
        profile.hometown = data.get('hometown', '')
        profile.college = data.get('college', '')
        profile.job_title = data.get('job_title', '')
        profile.education_level = data['education_level']
        profile.mbti = data['mbti']
        profile.constellation = data['constellation']
        profile.blood_type = data['blood_type']
        profile.religion = data['religion']
        profile.sexuality = data['sexuality']
        profile.ethnicity = data['ethnicity']
        profile.diet = data['diet']
        profile.smoke = data.get('smoke', 3)
        profile.drinking = data.get('drinking', 3)
        profile.marijuana = data.get('marijuana', 3)
        profile.drugs = data.get('drugs', 3)
        profile.skills = data.get('skills', [])
        profile.personalities = data.get('personalities', [])
        profile.languages = data.get('languages', [])
        profile.interest_types = data.get('interest_types', [])

        current_app.logger.info(f"Serialized profile: {profile.serialize()}")

        try:
            if create_profile:
                db.session.add(profile)
            db.session.commit()
            current_app.logger.info('Profile for user_id %s created successfully', user_id)

            return jsonify_response({'message': f"User {user_id} profile created/updated successfully"}, 201)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify_response({'error': str(e)}, 500)


@profile_ns.route('/view/<int:user_id>')
class ProfileView(Resource):
    @profile_ns.response(200, 'Profile retrieved successfully.')
    @profile_ns.response(404, 'Profile not found')
    def get(self, user_id):
        profile = Profile.query.get_or_404(user_id)
        current_app.logger.info(f"Profile retrieved: {profile.serialize()}")
        return jsonify_response(profile.serialize(), 200)
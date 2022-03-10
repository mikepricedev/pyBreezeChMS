from strenum import StrEnum


class EndPoints(StrEnum):
    PEOPLE = '/api/people'
    EVENTS = '/api/events'
    PROFILE_FIELDS = '/api/profile'
    CONTRIBUTIONS = '/api/giving'
    ATTENDANCE = '/api/events/attendance'
    VOLUNTEERS = '/api/volunteers'
    FUNDS = '/api/funds'
    FORMS = '/api/forms'
    PLEDGES = '/api/pledges'
    TAGS = '/api/tags'
    BREEZE_ACCOUNT = '/api/account'

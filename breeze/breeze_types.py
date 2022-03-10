from enum import Enum, auto
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, TypedDict


Id = Union[int, str]
ProfileFields = List[Dict]


class FamilyMemberDetails(TypedDict):
    id: int
    first_name: str
    force_first_name: str
    last_name: str
    thumb_path: str
    path: str


class FamilyMember(TypedDict):
    id: int
    oid: int
    person_id: int
    family_id: int
    family_role_id: int
    created_on: datetime
    role_name: str
    role_id: int
    order: int
    details: FamilyMemberDetails


PersonDetails = Dict[Union[int, str], Any]


class Person(TypedDict):
    id: int
    first_name: str
    force_first_name: str
    last_name: str
    maiden_name: str
    middle_name: str
    nick_name: str
    path: str
    details: Optional[PersonDetails]
    family: Optional[List[FamilyMember]]


class ProfileFieldOption(TypedDict):
    id: int
    oid: int
    option_id: int
    profile_field_id: int
    name: str
    position: int
    profile_id: Union[int, str]
    created_on: datetime


class ProfileField(TypedDict):
    id: int
    oid: int
    field_id: int
    profile_section_id: int
    field_type: str
    name: str
    position: int
    profile_id: Union[int, str]
    created_on: datetime
    options: Optional[List[ProfileFieldOption]]


class ProfileFields(TypedDict):
    id: int
    column_id: int
    created_on: datetime
    name: str
    position: int
    profile_id: Union[str, int]
    section_id: int
    fields: List[ProfileField]


class Tag(TypedDict):
    id: int
    name: str
    created_on: datetime
    folder_id: int


class TagFolder(TypedDict):
    id: int
    created_on: datetime
    name: str
    parent_id: int


class Attendance(TypedDict):
    instance_id: int
    person_id: int
    check_out: Union[None, datetime]
    created_on: datetime
    details: Optional[Dict[str, Any]]


class Calendar(TypedDict):
    id: int
    address: str
    color: str
    created_on: datetime
    embed_key: str
    name: str
    oid: int


class Location(TypedDict):
    id: int
    name: str


class ContributionFund(TypedDict):
    id: int
    oid: int
    payment_id: int
    fund_id: int
    amount: float
    created_on: datetime
    fund_name: str
    fund_custom_id: Union[str, int]
    tax_deductible: bool


class Contribution(TypedDict):
    id: int
    amount: float
    batch_name: str
    created_on: datetime
    envelope_number: Union[None, str, int]
    first_name: str
    last_name: str
    meta: Any
    method: Union[str, int]
    method_id: int
    note: str
    num: int
    paid_on: datetime
    person_id: int
    funds: List[ContributionFund]


class Fund(TypedDict):
    id: int
    archived: bool
    created_on: datetime
    custom_id: Union[int, str]
    group_id: int
    is_default: bool
    name: str
    tax_deductible: bool
    total: Optional[float]
    updated_at: datetime


class Campaign(TypedDict):
    id: int
    oid: int
    name: str
    created_on: datetime
    number_of_pledges: int
    total_pledged: float


class Pledge(TypedDict):
    id: int
    oid: int
    person_id: int
    fundraiser_id: int
    amount: float
    started_on: datetime
    ends_type: str
    ends_date: datetime
    ends_number: int
    frequency: str
    fund_ids_json: str
    note: str
    include_family: int
    created_on: datetime
    first_name: str
    last_name: str
    fundraiser_name: str
    total_pledged: float
    family_id: Union[None, int]
    total_paid: Union[None, float]
    paid_percent: float


class EventDetails(TypedDict):
    event_description: Optional[Union[Dict[str, Any], str]]
    label: Dict[str, Any]
    account_settings_modal_username: Optional[str]
    account_settings_modal_first_name: Optional[str]
    account_settings_modal_last_name: Optional[str]
    account_settings_modal_email: Optional[str]
    input_event_name: Optional[str]
    input_date: Optional[datetime]
    input_starts_on: Optional[Union[datetime, str]]
    input_starts_on_time: Optional[str]
    input_ends_on: Optional[Union[datetime, str]]
    input_ends_on_time: Optional[str]
    input_all_day: Optional[bool]
    input_event_repeats: Optional[bool]
    input_repeat_units: Optional[str]
    repeat_every: Optional[Dict[str, Any]]
    input_day_of_the_month: Optional[str]
    input_day_of_the_year: Optional[str]
    input_repeat_ends: Optional[str]
    input_end_on_date: Optional[Union[str, datetime]]
    check_in_print: Optional[bool]
    check_in_print_parent: Optional[bool]
    check_in_print_additional_name_tag: Optional[bool]
    nametag_id: Optional[Union[str, Dict[str, Any]]]
    check_out: Optional[bool]
    by_family: Optional[bool]
    add_person_fields: Optional[bool]
    selected_fields_json: Optional[str]
    show_tag_name_on_check_in: Optional[bool]
    disable_thumbnail: Optional[Dict[str, Any]]
    provider: Optional[str]
    check_in: Optional[str]
    location_ids_json: Optional[str]
    mode: Optional[str]
    is_locked: Optional[Union[bool, str]]
    category_id: Optional[Dict[str, Any]]
    appearance: Optional[str]
    default_mode: Optional[str]
    password_for_settings: Optional[bool]
    enable_thumbnail: Optional[bool]
    overwrite_future_events: Optional[str]
    event_id: Optional[Dict[str, Any]]
    instance_id: Optional[Dict[str, Any]]
    check_in_print_tags: Optional[Union[str, Dict[str, Any]]]
    check_in_print_parent_tags: Optional[Union[str, Dict[str, Any]]]
    check_in_print_additional_tags: Optional[Union[str, Dict[str, Any]]]
    selected_repeat_unit: Optional[str]
    repeat_frequency: Optional[str]
    selected_days: Optional[str]
    selected_dates: Optional[str]
    selected_months: Optional[str]
    specific_dates: Optional[str]
    repeat_ends: Optional[str]
    end_after_num_occurrences: Optional[str]
    monthly_each: Optional[str]
    on_the: Optional[str]
    on_the_second: Optional[str]
    on_the_month: Optional[str]
    on_the_month_second: Optional[str]
    check_in_tags: Optional[str]
    input_repeat_end_on_date: Optional[datetime]
    event_frequency: Optional[str]
    input_repeat_every: Optional[Dict[str, Any]]
    input_repeat_week_on: Optional[Dict[str, Any]]
    check_in_forms: Optional[str]
    specific_date_1: Optional[datetime]
    event_repeat_specific_dates: Optional[str]
    repeat_month_type: Optional[str]
    input_repeat_month_each: Optional[Dict[str, Any]]


class Event(TypedDict):
    id: int
    category_id: int
    created_on: datetime
    end_datetime: datetime
    event_id: int
    is_modified: bool
    name: str
    oid: int
    settings_id: int
    start_datetime: datetime
    details: Optional[EventDetails]


FormEntryResponse = Dict[int, Any]


class Form(TypedDict):
    id: int
    created_on: datetime
    folder_id: int
    is_archived: bool
    name: str
    url_slug: str


class FormEntry(TypedDict):
    id: int
    oid: int
    form_id: int
    created_on: datetime
    person_id: Union[int, None]
    response: FormEntryResponse


class FormFieldOption(TypedDict):
    id: int
    oid: int
    option_id: int
    profile_field_id: int
    name: str
    position: int
    profile_id: Union[str, int]
    created_on: datetime


class FormField(TypedDict):
    id: int
    oid: int
    field_id: int
    profile_section_id: int
    field_type: str
    name: str
    position: int
    profile_id: Union[str, int]
    created_on: datetime
    options: Optional[List[FormFieldOption]]


class Volunteer(TypedDict):
    id: int
    oid: int
    instance_id: int
    person_id: int
    response: int
    comment: str
    rsvped_on: Union[None, datetime]
    created_on: datetime
    role_ids: Union[None, List[int]]


class VolunteerRole(TypedDict):
    id: int
    role_id: int
    role_name: str
    quantity: Optional[int]


class AccountSummeryDetailsCountry(TypedDict):
    id: int
    name: str
    abbreviation: str
    abbreviation_2: str
    currency: str
    currency_symbol: str
    date_format: str
    sms_prefix: Union[int, str]


class AccountSummeryDetails(TypedDict):
    timezone: str
    country: AccountSummeryDetailsCountry


class AccountSummery(TypedDict):
    id: int
    name: str
    subdomain: str
    status: int
    created_on: datetime
    details: AccountSummeryDetails


class AccountLogActions(Enum):
    # Communications,
    email_sent = auto(),
    text_sent = auto(),
    # Contributions,
    contribution_added = auto(),
    contribution_updated = auto(),
    contribution_deleted = auto(),
    bulk_contributions_deleted = auto(),
    envelope_created = auto(),
    envelope_updated = auto(),
    envelope_deleted = auto(),
    payment_method_updated = auto(),
    payment_method_deleted = auto(),
    payment_method_created = auto(),
    bank_account_added = auto(),
    bank_account_updated = auto(),
    transfer_day_changed = auto(),
    bank_account_deleted = auto(),
    payment_association_deleted = auto(),
    payment_association_created = auto(),
    bulk_import_contributions = auto(),
    bulk_import_pledges = auto(),
    bulk_pledges_deleted = auto(),
    batch_updated = auto(),
    batch_deleted = auto(),
    bulk_envelopes_deleted = auto(),
    # Events,
    event_created = auto(),
    event_updated = auto(),
    event_deleted = auto(),
    event_instance_deleted = auto(),
    event_future_deleted = auto(),
    events_calendar_created = auto(),
    events_calendar_updated = auto(),
    events_calendar_deleted = auto(),
    bulk_import_attendance = auto(),
    attendance_deleted = auto(),
    bulk_attendance_deleted = auto(),
    # Volunteers,
    volunteer_role_created = auto(),
    volunteer_role_deleted = auto(),
    # People,
    person_created = auto(),
    person_updated = auto(),
    person_deleted = auto(),
    person_archived = auto(),
    person_merged = auto(),
    people_updated = auto(),
    bulk_update_people = auto(),
    bulk_people_deleted = auto(),
    bulk_people_archived = auto(),
    bulk_import_people = auto(),
    bulk_notes_deleted = auto(),
    # Tags,
    tag_created = auto(),
    tag_updated = auto(),
    tag_deleted = auto(),
    bulk_tags_deleted = auto(),
    tag_folder_created = auto(),
    tag_folder_updated = auto(),
    tag_folder_deleted = auto(),
    tag_assign = auto(),
    tag_unassign = auto(),
    # Forms,
    form_created = auto(),
    form_updated = auto(),
    form_deleted = auto(),
    form_entry_updated = auto(),
    form_entry_deleted = auto(),
    # Follow Ups,
    followup_option_created = auto(),
    followup_option_updated = auto(),
    followup_option_deleted = auto(),
    # Users,
    user_created = auto(),
    user_updated = auto(),
    user_deleted = auto(),
    role_created = auto(),
    role_updated = auto(),
    role_deleted = auto(),
    # Extensions,
    extension_installed = auto(),
    extension_uninstalled = auto(),
    extension_upgraded = auto(),
    extension_downgraded = auto(),
    # Account,
    sub_payment_method_updated = auto()


class AccountLog(TypedDict):
    id: int
    oid: int
    user_id: int
    action: AccountLogActions
    object_json: Any
    details: Optional[Any]

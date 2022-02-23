import json
import re
from typing import Any, List, Union, Callable, TypeVar
from datetime import datetime
from .account_log_actions import AccountLogActions


class type_parsing:

    DATE_TIME_FORMAT_STR_PATTERNS = {
        "%Y-%m-%d %H:%M:%S": r"^\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}$",
        "%Y-%m-%d": r"^\d{4}-\d{2}-\d{2}$",
        "%d-%m-%Y": r"^\d{2}-\d{2}-\d{4}$",
        "%m/%d/%Y": r"^\d{2}\/\d{2}\/\d{4}$"
    }

    DATE_TIME_FORMAT_STRINGS = {
        "YYYY-MM-DD hh:mm:ss": "%Y-%m-%d %H:%M:%S",
        "YYYY-MM-DD": "%Y-%m-%d",
        "DD-MM-YYYY": "%d-%m-%Y",
        "MM/DD/YYYY": "%m/%d/%Y"
    }

    # Dates
    @staticmethod
    def date_to_str(date: datetime, format_str_or_key: str) -> str:
        return date.strftime(
            type_parsing.DATE_TIME_FORMAT_STRINGS.get(
                format_str_or_key, format_str_or_key))

    @staticmethod
    def str_to_date(date):
        if not date:
            return date
        elif isinstance(date, str):
            for format_str, regex in type_parsing.DATE_TIME_FORMAT_STR_PATTERNS.items():
                if bool(re.match(regex, date)):
                    try:
                        return datetime.strptime(date, format_str)
                    except ValueError:
                        return None
                    except Exception as e:
                        raise e
        return date

    # bool
    @staticmethod
    def to_bool(bool_val: Union[bool, str, float, int]):
        if isinstance(bool_val, bool):
            return bool_val
        elif bool_val == "1" or bool_val == "true" or bool_val == "on" or bool_val == 1:
            return True
        elif bool_val == "0" or bool_val == "false" or bool_val == "off" or bool_val == 0:
            return False
        else:
            return bool_val

    # ids
    @staticmethod
    def id(id: Union[int, str]):
        if isinstance(id, str) and bool(re.match(r"^[0-9]+$", id)):
            return int(id)

        return id

    # ints
    @staticmethod
    def str_to_int(int_str: Union[int, float, str]):
        if isinstance(int_str, str) and bool(re.match(r"^-?[0-9]+$", int_str)):
            num = int(int_str)
            # Do not convert int greater than 64bit. Note: python 3 ints are
            # bonded only by memory
            if num.bit_length() <= 63:
                return num
            else:
                return int_str
        else:
            return int_str

    # floats
    @staticmethod
    def str_to_float(float_str: Union[int, float, str]):
        if isinstance(float_str, str) and bool(re.match(r"^-?[0-9]*\.[0-9]+$", float_str)):
            return float(float_str)
        else:
            return float_str


class ReturnTypeParsers(object):

    def _loads_double_stringified_(self, value: str):
        attempts = 0
        while isinstance(value, str) and attempts < 2:
            value = json.loads(value)
            attempts = attempts + 1
        return value

    def _unknown_value_formatter_(self, key, value):

        def recursive_formatter(key: str, value):
            return self._unknown_value_formatter_(key, value)

        if isinstance(value, dict):
            return self._parse_types_(to_parse=value,
                                      custom_type_parser=recursive_formatter)
        elif isinstance(value, list):
            return list(map(
                lambda item: recursive_formatter("_", item),
                value
            ))

        return self._known_types_formatter_(key, value)

    def _known_types_formatter_(self, key: str, value):
        # ids
        if key == "id" or key == "oid" or bool(re.search(r"_id",
                                                         key, re.S)):
            return type_parsing.id(value)
        # strings
        elif isinstance(value, str):
            # ints
            value = type_parsing.str_to_int(int_str=value)
            if isinstance(value, int):
                return value
            # floats
            value = type_parsing.str_to_float(float_str=value)
            if isinstance(value, float):
                return value

        return type_parsing.str_to_date(date=value)

    def _parse_types_(self, to_parse, custom_type_parser: Callable[[
        TypeVar(name="key", bound=str),
        TypeVar(name="value")
    ], Any] = None):
        if isinstance(to_parse, list):

            return list(map(
                lambda _to_parse: self._parse_types_(to_parse=_to_parse),
                to_parse
            ))
        elif isinstance(to_parse, dict):
            for key, value in to_parse.items():
                if custom_type_parser:
                    value = custom_type_parser(key=key, value=value)

                # known formats
                value = self._known_types_formatter_(key=key, value=value)

                to_parse[key] = value
            return to_parse

        return self._known_types_formatter_(key="_", value=to_parse)

    def person_family(self, family_member: dict) -> dict:

        def family_parser(key: str, value):
            # details
            if "details" == key and isinstance(value, dict):
                return self.person(person=value)

            return self._unknown_value_formatter_(key=key, value=value)

        return self._parse_types_(to_parse=family_member,
                                  custom_type_parser=family_parser)

    def person_details_email(self, email: dict) -> dict:

        def email_formater(key: str, value):
            # bool
            if "is_primary" == key:
                return type_parsing.to_bool(value)

            elif "allow_bulk" == key:
                return type_parsing.to_bool(value)

            elif "is_private" == key:
                return type_parsing.to_bool(value)

            return value

        return self._parse_types_(to_parse=email, custom_type_parser=email_formater)

    def person_details_phone(self, phone: dict) -> dict:

        def phone_formatter(key: str, value):
            if "do_not_text" == key:
                return type_parsing.to_bool(value)

            elif "is_private" == key:
                return type_parsing.to_bool(value)

            return value

        return self._parse_types_(to_parse=phone,
                                  custom_type_parser=phone_formatter)

    def person_details_address(self, address: dict) -> dict:

        def address_formatter(key: str, value):
            if "is_primary" == key:
                return type_parsing.to_bool(value)

            if "is_private" == key:
                return type_parsing.to_bool(value)

            return value

        return self._parse_types_(to_parse=address,
                                  custom_type_parser=address_formatter)

    def _profile_fields_parsering_ids_lookup(self,
                                             profile_fields: List[dict]) -> dict:
        email_field_ids: set[str] = set()
        phone_field_ids: set[str] = set()
        address_field_ids: set[str] = set()

        for field_group in profile_fields:
            for field in field_group.get("fields", []):
                field_type: str = field.get("field_type", None)
                field_id: str = field.get("field_id", None)
                if not field_id or not field_type:
                    continue
                elif field_type == "email":
                    email_field_ids.add(str(field_id))
                elif field_type == "phone":
                    phone_field_ids.add(str(field_id))
                elif field_type == "address":
                    address_field_ids.add(str(field_id))
        return {
            "email_field_ids": email_field_ids,
            "phone_field_ids": phone_field_ids,
            "address_field_ids": address_field_ids
        }

    def person_details(self, details: dict, parsing_ids: dict) -> dict:

        def detail_formatter(key: str, value):
            if key in parsing_ids.get("email_field_ids"):
                if isinstance(value, list):
                    return list(map(
                        lambda email: self.person_details_email(email=email),
                        value
                    ))
                elif isinstance(value, dict):
                    return self.person_details_email(
                        email=value)
            elif key in parsing_ids.get("phone_field_ids"):
                if isinstance(value, list):
                    return list(map(
                        lambda phone: self.person_details_phone(phone=phone),
                        value
                    ))
                elif isinstance(value, dict):
                    return self.person_details_phone(
                        phone=value)
            elif key in parsing_ids.get("address_field_ids"):
                if isinstance(value, list):
                    return list(map(
                        lambda address: self.person_details_address(
                            address=address),
                        value
                    ))
                elif isinstance(value, dict):
                    return self.person_details_address(address=value)

            return self._unknown_value_formatter_(key=key, value=value)

        # known formats
        details = self._parse_types_(
            to_parse=details, custom_type_parser=detail_formatter)

        return details

    def _person(self, person: dict, parsing_ids: dict) -> dict:

        def person_formatter(key: str, value):
            if key == "family" and value and isinstance(value, list):
                return list(map(lambda family_member: self.person_family(
                    family_member), value))
            elif key == "details" and value and isinstance(value, dict):
                return self.person_details(details=value,
                                           parsing_ids=parsing_ids)

            return value

        person = self._parse_types_(to_parse=person,
                                    custom_type_parser=person_formatter)

        return person

    def person(self, person: Union[dict, list], profile_fields: List[dict] = []) -> Union[dict, list]:

        parsing_ids = self._profile_fields_parsering_ids_lookup(
            profile_fields=profile_fields)

        if isinstance(person, list):
            return list(map(
                lambda person: self._person(person=person,
                                            parsing_ids=parsing_ids),
                person
            ))
        else:
            return self._person(person=person,
                                parsing_ids=parsing_ids),

    def profile_field_option(self, option: dict) -> dict:
        return self._parse_types_(to_parse=option)

    def profile_sub_field(self, sub_field: dict) -> dict:

        def sub_field_parser(key: str, value):
            if "options" == key:
                if value:
                    return list(map(
                        lambda option: self.profile_field_option(
                            option),
                        value
                    ))

            return value

        return self._parse_types_(to_parse=sub_field,
                                  custom_type_parser=sub_field_parser)

    def profile_field(self, profile_field: dict) -> dict:

        def field_parser(key: str, value):
            if "fields" == key:
                if value:
                    return list(map(
                        lambda field: self.profile_sub_field(
                            field),
                        value
                    ))

            return value

        return self._parse_types_(to_parse=profile_field,
                                  custom_type_parser=field_parser)

    def tag(self, tag: dict) -> dict:
        return self._parse_types_(to_parse=tag)

    def tag_folder(self, tag_folder: dict) -> dict:
        return self._parse_types_(to_parse=tag_folder)

    def event_details(self, event_details: dict) -> dict:

        def details_parser(key: str, value):
           # bool
            if "input_event_repeats" == key:
                return type_parsing.to_bool(value)

            elif "input_all_day" == key:
                return type_parsing.to_bool(value)

            elif "check_in_print" == key:
                return type_parsing.to_bool(value)

            elif "check_in_print_parent" == key:
                return type_parsing.to_bool(value)

            elif "check_in_print_additional_name_tag" == key:
                return type_parsing.to_bool(value)

            elif "password_for_settings" == key:
                return type_parsing.to_bool(value)

            elif "check_out" == key:
                return type_parsing.to_bool(value)

            elif "by_family" == key:
                return type_parsing.to_bool(value)

            elif "add_person_fields" == key:
                return type_parsing.to_bool(value)

            elif "show_tag_name_on_check_in" == key:
                return type_parsing.to_bool(value)

            elif "enable_thumbnail" == key:
                return type_parsing.to_bool(value)

            elif "is_locked" == key:
                return type_parsing.to_bool(value)

            return self._unknown_value_formatter_(key=key, value=value)

        return self._parse_types_(to_parse=event_details,
                                  custom_type_parser=details_parser)

    def event(self, event: dict) -> dict:

        def event_parser(key: str, value):
            # details
            if "details" == key:
                return self.event_details(
                    event_details=value)

            # bool
            elif "is_modified" == key:
                return type_parsing.to_bool(value)

            return self._unknown_value_formatter_(key=key, value=value)

        return self._parse_types_(to_parse=event,
                                  custom_type_parser=event_parser)

    def calendar(self, calendar: dict) -> dict:
        # known formats
        calendar = self._parse_types_(to_parse=calendar)

        return calendar

    def location(self, location: dict) -> dict:
        # known formats
        location = self._parse_types_(to_parse=location)

        return location

    def attendee(self, attendee: dict) -> dict:
        # known formats
        attendee = self._parse_types_(to_parse=attendee)
        return attendee

    def fund(self, fund: dict) -> dict:

        def fund_parser(key: str, value):
            if "tax_deductible" == key:
                return type_parsing.to_bool(value)

            elif "is_default" == key:
                return type_parsing.to_bool(value)

            elif "archived" == key:
                return type_parsing.to_bool(value)

            return self._unknown_value_formatter_(key=key, value=value)

        return self._parse_types_(to_parse=fund, custom_type_parser=fund_parser)

    def contribution(self, contribution: dict) -> dict:

        def contribution_parser(key: str, value):

            # funds
            if "funds" == key:
                if value:
                    return list(map(
                        lambda fund: self.fund(fund=fund),
                        value
                    ))

            # person
            elif "person" == key:
                if isinstance(value, dict):
                    return self.person(person=value)

            return self._unknown_value_formatter_(key=key, value=value)

        return self._parse_types_(to_parse=contribution,
                                  custom_type_parser=contribution_parser)

    def campaign(self, campaign: dict) -> dict:
        return self._parse_types_(to_parse=campaign)

    def pledge(self, pledge: dict) -> dict:
        return self._parse_types_(to_parse=pledge)

    def form(self, form: dict) -> dict:
        def form_parser(key: str, value):
            # bool
            if "is_archived" == key:
                return type_parsing.to_bool(value)

            return value

        return self._parse_types_(to_parse=form, custom_type_parser=form_parser)

    def form_field_option(self, option: dict) -> dict:
        return self._parse_types_(to_parse=option)

    def form_field(self, form_field: dict) -> dict:
        def field_parser(key: str, value):
            # options
            if "options" == key:
                if value:
                    return list(map(
                        lambda option: self.form_field_option(option=option),
                        value
                    ))

            return value

        return self._parse_types_(to_parse=form_field,
                                  custom_type_parser=field_parser)

    def form_entry_response(self, response: dict) -> dict:

        def entry_response_parser(key: str, value):
            return self._unknown_value_formatter_(key=key, value=value)

        return self._parse_types_(to_parse=response,
                                  custom_type_parser=entry_response_parser)

    def form_entry(self, entry: dict) -> dict:
        def entry_parser(key: str, value):
            if "response" == key:
                return self.form_entry_response(value)
            return value

        return self._parse_types_(to_parse=entry,
                                  custom_type_parser=entry_parser)

    def volunteer_role(self, role: dict) -> dict:
        # known formats
        role = self._parse_types_(to_parse=role)

        return role

    def volunteer(self, volunteer: dict) -> dict:
        # known formats
        volunteer = self._parse_types_(to_parse=volunteer)
        return volunteer

    def breeze_account(self, account: dict) -> dict:
        def account_parser(key: str, value):
            return self._unknown_value_formatter_(key=key, value=value)

        return self._parse_types_(to_parse=account,
                                  custom_type_parser=account_parser)

    def breeze_account_log_details(self, details, action: str):

        if not details:
            return details
        elif isinstance(details, str):
            try:
                details = json.loads(details)
            except:
                return details

        if not details:
            return details
        # tags
        elif AccountLogActions.tag_unassign.name == action or AccountLogActions.tag_assign.name == action:
            details = self._loads_double_stringified_(details)

        elif not (isinstance(details, dict) or isinstance(details, list)):
            return details

        # Contributions
        elif AccountLogActions.contribution_updated.name == action:
            if isinstance(details, list):
                return list(map(
                    lambda contribution: self.contribution(
                        contribution=contribution),
                    details
                ))
            elif isinstance(details, dict):
                return self.contribution(
                    contribution=details)
        elif AccountLogActions.contribution_deleted.name == action:
            return self.contribution(
                contribution=details)
        elif AccountLogActions.batch_deleted.name == action:
            def batch_deleted_parser(key: str, value):
                if "payments" == key:
                    return list(map(
                        lambda contribution: self.contribution(
                            contribution=contribution),
                        value
                    ))

                return value

            return self._parse_types_(to_parse=details,
                                      custom_type_parser=batch_deleted_parser)

        # Events
        elif AccountLogActions.event_created.name == action or AccountLogActions.event_updated.name == action:
            def event_created_parser(key: str, value):
                if key == "details_json":
                    try:
                        if isinstance(value, str):
                            return self._unknown_value_formatter_("_", json.loads(value))
                    except:
                        return value

                return value

            details = self.event(event=details)

            return self._parse_types_(to_parse=details,
                                      custom_type_parser=event_created_parser)

        def unknown_parser(key: str, value):
            return self._unknown_value_formatter_(key=key, value=value)

        return self._parse_types_(to_parse=details,
                                  custom_type_parser=unknown_parser)

    def breeze_account_log(self, account_log: dict) -> dict:
        action = account_log.get("action", None)

        def log_parser(key: str, value):
            if "object_json" == key:
                if isinstance(value, str):
                    if action == AccountLogActions.tag_unassign.name or action == AccountLogActions.tag_assign.name:
                        value = self._loads_double_stringified_(value)
                    else:
                        value = json.loads(value)

                return self._unknown_value_formatter_(key="_",
                                                      value=value)
            elif "details" == key:
                if action:
                    return self.breeze_account_log_details(
                        details=value, action=action)

            return self._unknown_value_formatter_(key=key, value=value)

        return self._parse_types_(to_parse=account_log,
                                  custom_type_parser=log_parser)

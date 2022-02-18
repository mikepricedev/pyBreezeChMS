from typing import List, Union
from datetime import datetime


class type_parsing:

    DATE_TIME_FORMAT_STRINGS = {
        "YYYY-MM-DD": "%Y-%m-%d",
        "YYYY-MM-DD hh:mm:ss": "%Y-%m-%d %H:%M:%S",
        "DD-MM-YYYY": "%d-%m-%Y",
        "MM/DD/YYYY": "%m/%d/%Y"
    }

    NULL_CASES = {
        "YYYY-MM-DD": "00-00-00",
        "YYYY-MM-DD hh:mm:ss": "00-00-00 00:00:00",
        "DD-MM-YYYY": "00-00-00",
        "MM/DD/YYYY": "00/00/00"
    }

    # Dates

    @staticmethod
    def date_to_str(date: datetime, format_str_or_key: str) -> str:
        return date.strftime(
            type_parsing.DATE_TIME_FORMAT_STRINGS.get(
                format_str_or_key, format_str_or_key))

    @staticmethod
    def str_to_date(date: str, format_str_or_key: str) -> Union[datetime, None]:

        format_str = type_parsing.DATE_TIME_FORMAT_STRINGS.get(
            format_str_or_key) if format_str_or_key in type_parsing.DATE_TIME_FORMAT_STRINGS else format_str_or_key

        # check for null dates
        if type_parsing.NULL_CASES.get(format_str) == date:
            return None

        return datetime.strptime(date,
                                 format_str)


class ReturnTypeParsers(object):

    def event_details(self, event_details: dict) -> dict:
        # dates
        if "input_date" in event_details:
            event_details["input_date"] = type_parsing.str_to_date(
                event_details.get("input_date"), "MM/DD/YYYY")
        if "input_starts_on" in event_details:
            event_details["input_starts_on"] = type_parsing.str_to_date(
                event_details.get("input_starts_on"), "MM/DD/YYYY")

        if "input_ends_on" in event_details:
            event_details["input_ends_on"] = type_parsing.str_to_date(
                event_details.get("input_ends_on"), "MM/DD/YYYY")

    def event(self, event: dict) -> dict:

        # dates
        if "start_datetime" in event:
            event["start_datetime"] = type_parsing.str_to_date(
                event.get("start_datetime"), "YYYY-MM-DD hh:mm:ss")

        if "end_datetime" in event:
            event["end_datetime"] = type_parsing.str_to_date(
                event.get("end_datetime"), "YYYY-MM-DD hh:mm:ss")

        if "created_on" in event:
            event["created_on"] = type_parsing.str_to_date(
                event.get("created_on"), "YYYY-MM-DD hh:mm:ss")

        if "details" in event:
            event["details"] = self.event_details(
                event_details=event.get("details"))

        return event

    def calendar(self, calendar: dict) -> dict:

        # dates
        if "created_on" in calendar:
            calendar["created_on"] = type_parsing.str_to_date(
                calendar.get("created_on"), "YYYY-MM-DD hh:mm:ss")

        return calendar

    def attendee(self, attendee: dict) -> dict:

        # dates
        if "created_on" in attendee:
            attendee["created_on"] = type_parsing.str_to_date(
                attendee.get("created_on"), "YYYY-MM-DD hh:mm:ss")

        if "check_in" in attendee:
            check_in = attendee.get("check_in")
            attendee["check_in"] = type_parsing.str_to_date(
                check_in, "YYYY-MM-DD hh:mm:ss")

        if "check_out" in attendee:
            check_out = attendee.get("check_out")
            attendee["check_out"] = type_parsing.str_to_date(
                check_out, "YYYY-MM-DD hh:mm:ss")

        return attendee

    def volunteer(self, volunteer: dict) -> dict:

        # dates
        if "created_on" in volunteer:
            volunteer["created_on"] = type_parsing.str_to_date(
                volunteer.get("created_on"), "YYYY-MM-DD hh:mm:ss")

        if "rsvped_on" in volunteer:
            rsvped_on = volunteer.get("rsvped_on")
            volunteer["rsvped_on"] = type_parsing.str_to_date(
                rsvped_on, "YYYY-MM-DD hh:mm:ss")

        return volunteer

    def person_family(self, family_member: dict) -> dict:
        # dates
        if "created_on" in family_member:
            family_member["created_on"] = type_parsing.str_to_date(
                family_member.get("created_on"), "YYYY-MM-DD hh:mm:ss")
        return family_member

    def person_details(self, details: dict, profile_fields: List[dict]) -> dict:

        date_field_ids: set[str] = set()
        birthday: str = None

        for field_group in profile_fields:
            for field in field_group.get("fields", []):
                field_type: str = field.get("field_type", None)
                field_id: str = field.get("field_id", None)
                if not field_id or not field_type:
                    continue
                elif field_type == "date":
                    date_field_ids.add(field_id)
                elif field_type == "birthdate":
                    birthday = field_id

        if birthday and birthday in details:
            details[birthday] = type_parsing.str_to_date(
                details.get(birthday), "YYYY-MM-DD")

        for date_field_id in date_field_ids:
            if date_field_id in details:
                details[date_field_id] = type_parsing.str_to_date(
                    details.get(date_field_id), "MM/DD/YYYY")

        return details

    def person(self, person: dict, profile_fields: List[dict] = None) -> dict:
        # dates
        if "created_on" in person:
            person["created_on"] = type_parsing.str_to_date(
                person.get("created_on"), "YYYY-MM-DD hh:mm:ss")

        if "family" in person:
            person["family"] = list(map(lambda family_member: self.person_family(
                family_member), person.get("family")))

        if "details" in person and profile_fields:
            person["details"] = self.person_details(
                person.get("details"), profile_fields)

        return person

    def profile_field_option(self, option: dict) -> dict:
        # dates
        if "created_on" in option:
            option["created_on"] = type_parsing.str_to_date(
                option.get("created_on"), "YYYY-MM-DD hh:mm:ss")

        return option

    def profile_sub_field(self, sub_field: dict) -> dict:

        # dates
        if "created_on" in sub_field:
            sub_field["created_on"] = type_parsing.str_to_date(
                sub_field.get("created_on"), "YYYY-MM-DD hh:mm:ss")

        if "options" in sub_field:
            sub_field["options"] = list(map(
                lambda option: self.profile_field_option(
                    option), sub_field.get("options")
            ))

        return sub_field

    def profile_field(self, profile_field: dict) -> dict:
        # dates
        if "created_on" in profile_field:
            profile_field["created_on"] = type_parsing.str_to_date(
                profile_field.get("created_on"), "YYYY-MM-DD hh:mm:ss")

        if "fields" in profile_field:
            profile_field["fields"] = list(map(
                lambda field: self.profile_sub_field(
                    field), profile_field.get("fields")
            ))

        return profile_field

    def fund(self, fund: dict) -> dict:
        # dates
        if "created_on" in fund:
            fund["created_on"] = type_parsing.str_to_date(
                fund.get("created_on"), "YYYY-MM-DD hh:mm:ss")

        if "updated_at" in fund:
            fund["updated_at"] = type_parsing.str_to_date(
                fund.get("updated_at"), "YYYY-MM-DD hh:mm:ss")

        # numbers
        if "amount" in fund:
            fund["amount"] = float(fund.get("amount"))

        return fund

    def contribution(self, contribution: dict) -> dict:
        # dates
        if "created_on" in contribution:
            contribution["created_on"] = type_parsing.str_to_date(
                contribution.get("created_on"), "YYYY-MM-DD hh:mm:ss")
        if "paid_on" in contribution:
            contribution["paid_on"] = type_parsing.str_to_date(
                contribution.get("paid_on"), "YYYY-MM-DD hh:mm:ss")

        # numbers
        if "amount" in contribution:
            contribution["amount"] = float(contribution.get("amount"))

        if "funds" in contribution:
            contribution["funds"] = list(map(
                lambda fund: self.fund(fund=fund),
                contribution.get("funds")
            ))

        return contribution

    def tag(self, tag: dict) -> dict:
        # dates
        if "created_on" in tag:
            tag["created_on"] = type_parsing.str_to_date(
                tag.get("created_on"), "YYYY-MM-DD hh:mm:ss")

        return tag

    def tag_folder(self, tag_folder: dict) -> dict:
        # dates
        if "created_on" in tag_folder:
            tag_folder["created_on"] = type_parsing.str_to_date(
                tag_folder.get("created_on"), "YYYY-MM-DD hh:mm:ss")

        return tag_folder

    def form(self, form: dict) -> dict:
        # dates
        if "created_on" in form:
            form["created_on"] = type_parsing.str_to_date(
                form.get("created_on"), "YYYY-MM-DD hh:mm:ss")

        return form

    def form_field_option(self, option: dict) -> dict:
        # dates
        if "created_on" in option:
            option["created_on"] = type_parsing.str_to_date(
                option.get("created_on"), "YYYY-MM-DD hh:mm:ss")

        return option

    def form_field(self, form_field: dict) -> dict:
        # dates
        if "created_on" in form_field:
            form_field["created_on"] = type_parsing.str_to_date(
                form_field.get("created_on"), "YYYY-MM-DD hh:mm:ss")

        # options
        if "options" in form_field:
            form_field["options"] = list(map(
                lambda option: self.form_field_option(option=option),
                form_field.get("options")
            ))

        return form_field

    def form_entry_response(self, response: dict,
                            form_fields: List[dict] = None) -> dict:

        date_field_ids: set[str] = set()

        if form_fields:

            for field in form_fields:
                field_type: str = field.get("field_type", None)
                field_id: str = field.get("field_id", None)
                if field_type and field_id and field_type == "date":
                    date_field_ids.add(field_id)

        for key, value in response.items():
            if key in date_field_ids:
                response[key] = type_parsing.str_to_date(value, "MM/DD/YYYY")
            elif isinstance(value, dict):
                if "created_on" in value:
                    value["created_on"] = type_parsing.str_to_date(
                        value.get("created_on"), "YYYY-MM-DD hh:mm:ss")

        return response

    def form_entry(self, entry: dict, form_fields: List[dict] = None) -> dict:
        # dates
        if "created_on" in entry:
            entry["created_on"] = type_parsing.str_to_date(
                entry.get("created_on"), "YYYY-MM-DD hh:mm:ss")

        if "response" in entry:
            entry["response"] = self.form_entry_response(
                entry.get("response"), form_fields)

        return entry

    def campaign(self, campaign: dict) -> dict:
        # dates
        if "created_on" in campaign:
            campaign["created_on"] = type_parsing.str_to_date(
                campaign.get("created_on"), "YYYY-MM-DD hh:mm:ss")

        # numbers
        if "total_pledged" in campaign:
            campaign["total_pledged"] = float(campaign.get("total_pledged"))

        if "number_of_pledges" in campaign:
            campaign["number_of_pledges"] = int(
                campaign.get("number_of_pledges"))

        return campaign

    def pledge(self, pledge: dict) -> dict:
        # dates
        if "created_on" in pledge:
            pledge["created_on"] = type_parsing.str_to_date(
                pledge.get("created_on"), "YYYY-MM-DD hh:mm:ss")

        if "started_on" in pledge:
            pledge["started_on"] = type_parsing.str_to_date(
                pledge.get("started_on"), "YYYY-MM-DD")

        if "ends_date" in pledge and "ends_type" in pledge and pledge.get("ends_type") == "date":
            pledge["ends_date"] = type_parsing.str_to_date(
                pledge.get("ends_date"), "YYYY-MM-DD")

        # numbers
        if "amount" in pledge:
            pledge["amount"] = float(pledge.get("amount"))

        if "total_pledged" in pledge:
            pledge["total_pledged"] = float(pledge.get("total_pledged"))

        if "total_paid" in pledge:
            pledge["total_paid"] = float(pledge.get("total_paid"))

        if "paid_percent" in pledge:
            pledge["paid_percent"] = float(pledge.get("paid_percent"))

        return pledge

    def breeze_account(self, account: dict) -> dict:
       # dates
        if "created_on" in account:
            account["created_on"] = type_parsing.str_to_date(
                account.get("created_on"), "YYYY-MM-DD hh:mm:ss")

        return account

    def breeze_account_log(self, account_log: dict) -> dict:
       # dates
        if "created_on" in account_log:
            account_log["created_on"] = type_parsing.str_to_date(
                account_log.get("created_on"), "YYYY-MM-DD hh:mm:ss")

        return account_log

"""Python wrapper for Breeze ChMS API: http://www.breezechms.com/api

This API wrapper allows churches to build custom functionality integrated with
Breeze Church Management System.

Usage:
  from breeze import breeze

  breeze_api = breeze.BreezeApi(
      breeze_url='https://demo.breezechms.com',
      breeze_api_key='5c2d2cbacg3...')
  people = breeze_api.get_people();

  for person in people:
    print '%s %s' % (person['first_name'], person['last_name'])
"""

__author__ = 'alexortizrosado@gmail.com (Alex Ortiz-Rosado)'

import imp
import json
import os
import logging
from typing import List, Literal, Union
import asyncio
import httpx
from datetime import datetime
import re

from .breeze_type_parsing import type_parsing, ReturnTypeParsers, JSONSerial
from .account_log_actions import AccountLogActions

from .utils import make_enum

ENDPOINTS = make_enum(
    'BreezeApiURL',
    PEOPLE='/api/people',
    EVENTS='/api/events',
    PROFILE_FIELDS='/api/profile',
    CONTRIBUTIONS='/api/giving',
    ATTENDANCE='/api/events/attendance',
    VOLUNTEERS='/api/volunteers',
    FUNDS='/api/funds',
    FORMS='/api/forms',
    PLEDGES='/api/pledges',
    TAGS='/api/tags',
    BREEZE_ACCOUNT='/api/account')

DATE_TIME_FORMAT_STRINGS = type_parsing.DATE_TIME_FORMAT_STRINGS


class BreezeError(Exception):
    """Exception for BreezeApi."""
    pass


Id = Union[int, str]


class BreezeApi(object):
    """A wrapper for the Breeze REST API."""

    return_type_parsers: ReturnTypeParsers

    def __init__(self,
                 breeze_sub_domain: str = None,
                 breeze_tld: Union[str, None] = "breezechms.com",
                 breeze_url: str = None,
                 breeze_api_key: str = None,
                 dry_run=False,
                 client=httpx.AsyncClient(verify=True),
                 return_type_parsers=ReturnTypeParsers(),
                 retries=10
                 ):
        """Instantiates the BreezeApi with your Breeze account information.

        Args:
          breeze_sub_domain: The sub domain portion of your organizations Breeze
              service url e.g. https://{sub_domain}.breezechms.com. Overridden
              by env var 'BREEZE_SUB_DOMAIN' and/or 'breeze_url'.

          breeze_tld: The breeze top level domain. Default: 'breezechms.com'.
              Overridden by env var 'BREEZE_TLD' and/or 'breeze_url'

          breeze_url: Fully qualified domain for your organizations Breeze
              service. Overridden by env var 'BREEZE_URL'.  Note when provided
              either by int argument or env var, 'breeze_sub_domain' and
              'breeze_tld' are ignored.

          breeze_api_key: Unique Breeze API key. Overriddent by env var
              'BREEZE_API_KEY'.  For instructions on finding your organizations
              API key, see: http://breezechms.com/docs#extensions_api.

          dry_run: Enable no-op mode, which disables requests from being made.
              When combined with debug, this allows debugging requests without
              affecting data in your Breeze account.

          client: Async requests compatible session.

          return_type_parsers: ReturnTypeParsers derived class.  To provide
              parsing for breeze types.  The Breeze API returns everything as a
              string.

          retries: How many times to retry a request after a 500 or timeout
              error.  The breeze api can be unreliable production random 500
              and timeout errors.
          """

        breeze_sub_domain = os.getenv(key="BREEZE_SUB_DOMAIN",
                                      default=breeze_sub_domain)

        breeze_tld = os.getenv(key="BREEZE_TLD",
                               default=breeze_tld)

        breeze_url = os.getenv(key="BREEZE_URL",
                               default=breeze_url)

        breeze_api_key = os.getenv(key="BREEZE_API_KEY",
                                   default=breeze_api_key)

        if not breeze_api_key:
            error_msg = "Breeze api key not found.  Provided api key in init arg 'breeze_api_key' or in the env var 'BREEZE_API_KEY'"

            logging.exception(error_msg)
            raise BreezeError(error_msg)

        if not breeze_url:
            if not breeze_tld or not breeze_sub_domain:
                if not breeze_tld and not breeze_sub_domain:
                    error_msg = "Breeze url not found.  Provided your orgs full breeze url in the init arg 'breeze_url' or in the env var 'BREEZE_URL'. Alternatively provided the breeze tdl and your orgs breeze subdomain in the init args 'breeze_sub_domain' and 'breeze_tld' or in the env vars 'BREEZE_SUB_DOMAIN' and 'BREEZE_TLD'."

                    logging.exception(error_msg)
                    raise BreezeError(error_msg)

                elif not breeze_tld:
                    error_msg = "Breeze url not found.  Provided your orgs full breeze url in the init arg 'breeze_url' or in the env var 'BREEZE_URL'. Alternatively provided the breeze tdl in the init arg 'breeze_tld' or in the env var 'BREEZE_TLD'."

                    logging.exception(error_msg)
                    raise BreezeError(error_msg)

                else:
                    error_msg = "Breeze url not found.  Provided your orgs full breeze url in the init arg 'breeze_url' or in the env var 'BREEZE_URL'. Alternatively provided your orgs breeze subdomain in the init arg 'breeze_sub_domain' or in the env var 'BREEZE_SUB_DOMAIN'."

                    logging.exception(error_msg)
                    raise BreezeError(error_msg)
            else:
                breeze_url = f"https://{breeze_sub_domain}.{breeze_tld}"

        self.breeze_url = breeze_url
        self.breeze_api_key = breeze_api_key
        self.dry_run = dry_run
        self.client = client
        self.return_type_parsers = return_type_parsers
        self.retries = retries

        if not (self.breeze_url and self.breeze_url.startswith('https://') and
                self.breeze_url.find('.breezechms.')):
            logging.exception(
                'You must provide your breeze_url as subdomain.breezechms.com')
            raise BreezeError('You must provide your breeze_url as ',
                              'subdomain.breezechms.com')

    async def _request(self, endpoint, params=None, headers=None, timeout=60, attempts=0):
        """Makes an HTTP request to a given url.

        Args:
          endpoint: URL where the service can be accessed.
          params: Query parameters to append to endpoint url.
          headers: HTTP headers; used for authenication parameters.
          timeout: Timeout in seconds for HTTP request.

        Returns:
          HTTP response

        Throws:
          BreezeError if connection or request fails."""
        if headers is None:
            headers = {}
        headers.update({
            'Content-Type': 'application/json',
            'Api-Key': self.breeze_api_key}
        )

        if params is None:
            params = {}
        keywords = dict(params=params, headers=headers, timeout=timeout)
        url = '%s%s' % (self.breeze_url, endpoint)

        logging.debug('Making request to %s', url)
        if self.dry_run:
            return
        response: httpx.Response = None
        try:
            response = await self.client.get(url, ** keywords)

            # The breeze api server can be unreliable producing random
            #  500 errors
            if response.status_code >= 500 and attempts < self.retries:
                attempts = attempts + 1
                logging.warning(
                    f"Error Code {response.status_code}: {url}.  Retry attempt number {attempts} of {self.retries}.")
                # sleep for 100 ms for each retry for a max of 1000ms
                await asyncio.sleep(min((attempts/10), 1))
                return await self._request(endpoint=endpoint,
                                           params=params,
                                           headers=headers,
                                           timeout=timeout,
                                           attempts=attempts)

            response = response.json()
        except httpx.ReadTimeout as error:
            if attempts < self.retries:
                attempts = attempts + 1
                logging.warning(
                    f"Read Timeout Error: {url}.  Retry attempt number {attempts} of {self.retries}.")
                # sleep for 100 ms for each retry for a max of 1000ms
                await asyncio.sleep(min((attempts/10), 1))
                return await self._request(endpoint=endpoint,
                                           params=params,
                                           headers=headers,
                                           timeout=timeout,
                                           attempts=attempts)
            else:
                raise error
        except (httpx.RequestError, Exception) as error:
            logging.exception(str(error))
            raise BreezeError(error)
        else:
            if not self._request_succeeded(response):
                logging.exception(str(response))
                raise BreezeError(response)
            logging.debug('JSON Response: %s', response)
            return response

    def _request_succeeded(self, response):
        """Predicate to ensure that the HTTP request succeeded."""
        if isinstance(response, bool):
            return response
        else:
            try:
                iter(response)
            except TypeError:
                return True

            return not (('errors' in response) or ('errorCode' in response))

    async def _list_people(self,
                           details: bool = False,
                           has_tags: List[Id] = None,
                           does_not_have_tags: List[Id] = None,
                           archived: bool = False,
                           limit: int = None,
                           offset: int = 0,
                           **filter):

        params = []

        if len(filter):
            for key in list(filter.keys()):
                if bool(re.match(r'^_[0-9]+', key)):
                    filter[key[1:]] = filter.pop(key)

        if limit:
            params.append(f"limit={limit}")
        if offset or offset == 0:
            params.append(f"offset={max(offset,0)}")

        if has_tags:
            filter["tag_contains"] = '-'.join(
                map(
                    lambda tag_id: f'y_{tag_id}',
                    has_tags
                )
            )

        if does_not_have_tags:
            filter["tag_does_not_contain"] = '-'.join(
                map(
                    lambda tag_id: f'n_{tag_id}',
                    does_not_have_tags
                )
            )

        if archived:
            filter["archived"] = "yes"

        if len(filter):
            params.append(f'filter_json={json.dumps(filter)}')

        if details:

            # Bug breeze will not return details on list if archived
            if archived:

                (people, profile_fields) = await asyncio.gather(
                    self._request(
                        f"{ENDPOINTS.PEOPLE}/?{'&'.join(params)}"),
                    self.list_profile_fields()
                )

                if not people:
                    return []

                results = []
                promises = []
                for person in people:
                    person_id = type_parsing.id(id=person.get("id"))

                    promises.append(self._show_person(
                        person_id=person_id, details_or_profile_fields=profile_fields))

                    if len(promises) > 100:
                        results.extend(await asyncio.gather(*promises))
                        promises.clear()

                results.extend(await asyncio.gather(*promises))

                return results

            else:
                params.append('details=1')
                (people, profile_fields) = await asyncio.gather(
                    self._request(
                        f"{ENDPOINTS.PEOPLE}/?{'&'.join(params)}"),
                    self.list_profile_fields()
                )

                if not people:
                    return []

                return self.return_type_parsers.person(person=people,
                                                       profile_fields=profile_fields)

        else:
            params.append('details=0')
            people = (await self._request(
                f"{ENDPOINTS.PEOPLE}/?{'&'.join(params)}") or [])
            return self.return_type_parsers.person(person=people)

    async def list_people(self,
                          details: bool = False,
                          limit: int = None,
                          offset: int = 0):
        """List people from your database.
        Args:
            details: Option to return all information(slower) or just names.

            limit: Number of people to return. If None, will return all people.

            offset: Number of people to skip before beginning to return results.
                Can be used in conjunction with limit for pagination.

        returns:
          JSON response. For example:
          {
            "id": "157857",
            "first_name": "Thomas",
            "last_name": "Anderson",
            "path": "img\/profiles\/generic\/blue.jpg"
          },
          {
            "id": "157859",
            "first_name": "Kate",
            "last_name": "Austen",
            "path": "img\/profiles\/upload\/2498d7f78s.jpg"
          },
          {
            ...
          }"""

        params = []

        if limit:
            params.append(f"limit={limit}")
        if offset or offset == 0:
            params.append(f"offset={max(offset,0)}")

        if details:

            params.append('details=1')
            (people, profile_fields) = await asyncio.gather(
                self._request(
                    f"{ENDPOINTS.PEOPLE}/?{'&'.join(params)}"),
                self.list_profile_fields()
            )

            if not people:
                return []

            return self.return_type_parsers.person(person=people,
                                                   profile_fields=profile_fields)

        else:
            params.append('details=0')
            people = (await self._request(
                f"{ENDPOINTS.PEOPLE}/?{'&'.join(params)}") or [])
            return self.return_type_parsers.person(person=people)

    async def list_people_by_filters(self,
                                     details: bool = False,
                                     has_tags: List[Id] = None,
                                     does_not_have_tags: List[Id] = None,
                                     archived: bool = False,
                                     **filter):
        """List people from your database by a filters.
        Args:
            details: Option to return all information(slower) or just names.

            has_tags: Include people with these tags.

            does_not_have_tags: Include people without these tags.

            archived:  When 'True' return people who are archived.

            filter: Refer to the URL bar when filtering for people within
                Breeze's people filter page and use the 'key=value&...' you see
                listed.  When a filter key begins with a number you may add leading
                underscore to the filter key to create a valid python variable
                name.  Warning: 'has_tags', 'does_not_have_tags', and 'archived'
                will override corresponding filters.

        returns:
          JSON response. For example:
          {
            "id": "157857",
            "first_name": "Thomas",
            "last_name": "Anderson",
            "path": "img\/profiles\/generic\/blue.jpg"
          },
          {
            "id": "157859",
            "first_name": "Kate",
            "last_name": "Austen",
            "path": "img\/profiles\/upload\/2498d7f78s.jpg"
          },
          {
            ...
          }"""

        return await self._list_people(details=details,
                                       has_tags=has_tags,
                                       does_not_have_tags=does_not_have_tags,
                                       archived=archived,
                                       **filter)

    async def list_profile_fields(self):
        """List profile fields from your database.

        Returns:
          JSON response."""
        return list(map(
            lambda profile_field: self.return_type_parsers.profile_field(
                profile_field=profile_field),
            (await self._request(ENDPOINTS.PROFILE_FIELDS)) or []))

    async def _show_person(self,
                           person_id: Id,
                           details_or_profile_fields: Union[List[dict], bool]):
        params = []
        if details_or_profile_fields:
            params.append("details=1")

            async def get_results():
                if details_or_profile_fields == True:
                    return await asyncio.gather(
                        self._request(
                            f"{ENDPOINTS.PEOPLE}/{person_id}?{'&'.join(params)}"),
                        self.list_profile_fields()
                    )
                else:
                    person = await self._request(
                        f"{ENDPOINTS.PEOPLE}/{person_id}?{'&'.join(params)}")

                    return (person, details_or_profile_fields)

            (person, profile_fields) = await get_results()

            if person:
                return self.return_type_parsers.person(
                    person=person,
                    profile_fields=profile_fields)
            else:
                return None

        else:
            params.append("details=0")

            person = await self._request(f"{ENDPOINTS.PEOPLE}/{person_id}?{'&'.join(params)}")

            if not person:
                return None

            return self.return_type_parsers.person(person=person)

    async def show_person(self, person_id: Id, details: bool = True):
        """Retrieve the details for a specific person by their ID.

        Args:
          person_id: Unique id for a person in Breeze database.
          details: Option to return all information(slower) or just names. True = get all information pertaining to person; False = only get id and name

        Returns:
          JSON response."""
        return await self._show_person(person_id=person_id,
                                       details_or_profile_fields=details)

    async def list_tags(self, folder_id: Id = None):
        """List of tags

        Args:
          folder_id: If provided, only tags within that folder will be returned.

        Returns:
          JSON response. For example:
            [
            {
                "id": "523928",
                "name": "4th & 5th",
                "created_on": "2018-09-10 09:19:40",
                "folder_id": "1539"
            },
            {
                "id": "51994",
                "name": "6th Grade",
                "created_on": "2018-02-06 06:40:40",
                "folder_id": "1539"
            },
            {...}
            ]"""

        params = []
        if folder_id:
            params.append('folder_id=%s' % folder_id)

        return list(map(
            lambda tag: self.return_type_parsers.tag(tag=tag),
            (await self._request('%s/list_tags/?%s' % (ENDPOINTS.TAGS, '&'.join(params)))) or []
        ))

    async def list_tag_folders(self):
        """List of tag folders

        Args: (none)

        Returns:
          JSON response, for example:
             [
             {
                 "id": "1234567",
                 "parent_id": "0",
                 "name": "All Tags",
                 "created_on": "2018-06-05 18:12:34"
             },
             {
                 "id": "8234253",
                 "parent_id": "120425",
                 "name": "Kids",
                 "created_on": "2018-06-05 18:12:10"
             },
             {
                 "id": "1537253",
                 "parent_id": "5923042",
                 "name": "Small Groups",
                 "created_on": "2018-09-10 09:19:40"
             },
             {
                 "id": "20033",
                 "parent_id": "20031",
                 "name": "Student Ministries",
                 "created_on": "2018-12-15 18:11:31"
             }
             ]"""

        return list(map(
            lambda tag_folder: self.return_type_parsers.tag_folder(
                tag_folder=tag_folder),
            (await self._request("%s/list_folders" % ENDPOINTS.TAGS)) or []
        ))

    async def list_events(self,
                          start_date: datetime = None,
                          end_date: datetime = None,
                          category_id: Id = None,
                          eligible: bool = False,
                          details: bool = False,
                          limit: int = 500
                          ):
        """Retrieve a list of events based on search criteria.

        Args:
          start_date: Events on or after(YYYY-MM-DD)
          end_date: Events on or before(YYYY-MM-DD)
          category_id: If supplied, only events on the specified calendar will be returned. Note that external calendars are not available via this call.
          eligible: If set to 1, details about who is eligible to be checked in ("everyone", "tags", "forms", or "none") are returned(including tags associated with the event).
          details: If set to True, additional event details will be returned(e.g. description, check in settings, etc)
          limit: Number of events to return. Default is 500. Max is 1000.

        Returns:
          JSON response."""
        params = []
        if start_date:
            start_date = type_parsing.date_to_str(start_date, "YYYY-MM-DD")
            params.append(f"start={start_date}")
        if end_date:
            end_date = type_parsing.date_to_str(end_date, "YYYY-MM-DD")
            params.append(f"end={end_date}")
        if category_id:
            params.append(f"category_id={category_id}")
        if eligible:
            params.append("eligible=1")
        if details:
            params.append("details=1")
        if limit or limit == 0:
            params.append("limit={limit}")

        return list((map(
            lambda event: self.return_type_parsers.event(event=event),
            (await self._request('%s/?%s' % (ENDPOINTS.EVENTS, '&'.join(params)))) or []
        )))

    async def show_event(self,
                         instance_id: Id,
                         eligible: bool = False,
                         details: bool = False
                         ):
        """Retrieve a list of events based on search criteria.

          Args:
            instance_id: The id of the event instance that should be returned.

            eligible: If set to True, details about who is eligible to be checked in ("everyone", "tags", "forms", or "none") are returned (including tags associated with the event).

            details: If set to 1, additional event details will be returned (e.g. description, check in settings, etc).

        Returns:
          JSON response."""
        params = [f"instance_id={instance_id}"]
        if eligible:
            params.append("eligible=1")
        if details:
            params.append("details=1")

        event = (await self._request(f"{ENDPOINTS.EVENTS}/list_event?{'&'.join(params)}")) or None

        if event == None:
            return event
        else:
            return self.return_type_parsers.event(event=event)

    async def list_event_schedule(self,
                                  instance_id: Id,
                                  schedule_direction: Literal["before",
                                                              "after"] = "before",
                                  schedule_limit: int = 10,
                                  eligible: bool = False,
                                  details: bool = False
                                  ):
        """Retrieve a list of events from a series.

          Args:
            instance_id: The id of the event instance that should be returned.

            schedule_direction: If including the schedule, should it include events before the instance_id or after the instance_id.

            schedule_limit:  If including the schedule, how many events in the series should be returned. Default is 10. Max is 100.

            eligible: If set to True, details about who is eligible to be checked in ("everyone", "tags", "forms", or "none") are returned (including tags associated with the event).

            details: If set to 1, additional event details will be returned (e.g. description, check in settings, etc).

        Returns:
          JSON response."""
        params = [f"instance_id={instance_id}&schedule=1"]

        if schedule_direction:
            params.append(f"schedule_direction={schedule_direction}")
        if schedule_limit:
            params.append(f"schedule_limit={schedule_limit}")
        if eligible:
            params.append("eligible=1")
        if details:
            params.append("details=1")

        return list((map(
            lambda event: self.return_type_parsers.event(event=event),
            (await self._request(f"{ENDPOINTS.EVENTS}/list_event?{'&'.join(params)}")) or []
        )))

    async def list_calendars(self):
        """Retrieve a list of Calendars.
        """
        return list(map(
            lambda calendar: self.return_type_parsers.calendar(
                calendar=calendar),
            (await self._request(f"{ENDPOINTS.EVENTS}/calendars/list")) or []
        ))

    async def list_locations(self):
        """Retrieve a list of Locations.
        """
        return list(map(
            lambda location: self.return_type_parsers.location(
                location=location),
            (await self._request(f"{ENDPOINTS.EVENTS}/locations")) or []
        ))

    async def list_attendance(self, instance_id: Id, details: bool = False, type="person"):
        """Retrieve a list of attendees for a given event instance_id.

          Args:
            instance_id: The ID of the instance you'd like to return the attendance for
            details: If set to true, details of the person will be included in the response
            type: Determines if result should contain people or anonymous head count by setting to either 'person' or 'anonymous'

          Returns:
            JSON response."""

        params = [f"instance_id={instance_id}"]
        if details:
            params.append("details=1")
        if type:
            params.append(f"type={type}")

        return list(map(
            lambda attendee: self.return_type_parsers.attendee(
                attendee=attendee),
            (await self._request(f"{ENDPOINTS.ATTENDANCE}/list/?{'&'.join(params)}")) or []
        ))

    async def list_eligible_people(self, instance_id: Id):
        """Retrieve a list of eligible people for a give event instance_id.

          Args:
            instance_id: The ID of the instance you'd like to return the attendance for

          Returns:
            JSON response."""

        params = ['instance_id=%s' % instance_id, ]

        return list(map(
            lambda person: self.return_type_parsers.person(person=person),
            ((await self._request('%s/eligible?%s' %
                                  (ENDPOINTS.ATTENDANCE, '&'.join(params)), timeout=180)) or [])
        ))

    async def list_contributions(self,
                                 start_date: datetime = None,
                                 end_date: datetime = None,
                                 person_id: Id = None,
                                 include_family: bool = False,
                                 amount_min: Union[int, float] = None,
                                 amount_max: Union[int, float] = None,
                                 method_ids: List[Id] = None,
                                 fund_ids: List[Id] = None,
                                 envelope_number: Union[int, str] = None,
                                 batches: Union[int, str] = None,
                                 forms_ids: List[Id] = None,
                                 pledge_ids: List[Id] = None):
        """Retrieve a list of contributions.

        Args:
          start_date: Find contributions given on or after a specific date
                      (ie. 2015-1-1); required.
          end_date: Find contributions given on or before a specific date
                    (ie. 2018-1-31); required.
          person_id: ID of person's contributions to fetch. (ie. 9023482)
          include_family: Include family members of person_id(must provide
                          person_id); default: False.
          amount_min: Contribution amounts equal or greater than.
          amount_max: Contribution amounts equal or less than.
          method_ids: List of method IDs.
          fund_ids: List of fund IDs.
          envelope_number: Envelope number.
          batches: List of Batch numbers.
          forms: List of form IDs.
          pledge_ids: Pledge Campaign IDs. IDs accessible from list pledges query. Multiple ids separated by a dash(-).

        Returns:
          List of matching contributions.

        Throws:
          BreezeError on malformed request."""

        params = []
        if start_date:
            start_date = type_parsing.date_to_str(start_date, "DD-MM-YYYY")
            params.append(f"start={start_date}")
        if end_date:
            end_date = type_parsing.date_to_str(end_date, "DD-MM-YYYY")
            params.append(f"end={end_date}")
        if person_id:
            params.append('person_id=%s' % person_id)
        if include_family:
            if not person_id:
                logging.exception('include_family requires a person_id.')
                raise BreezeError('include_family requires a person_id.')
            params.append('include_family=1')
        if amount_min:
            params.append(f"amount_min={amount_min}")
        if amount_max:
            params.append(f"amount_max={amount_max}")
        if method_ids:
            params.append('method_ids=%s' % '-'.join(
                map(lambda id: str(id), method_ids)))
        if fund_ids:
            params.append('fund_ids=%s' % '-'.join(
                map(lambda id: str(id), fund_ids)))
        if envelope_number:
            params.append('envelope_number=%s' % envelope_number)
        if batches:
            params.append('batches=%s' % '-'.join(
                map(lambda id: str(id), batches)))
        if forms_ids:
            params.append('forms=%s' % '-'.join(
                map(lambda id: str(id), forms_ids)))
        if pledge_ids:
            params.append('pledge_ids=%s' % '-'.join(
                map(lambda id: str(id), pledge_ids)))

        return list(map(
            lambda contribution: self.return_type_parsers.contribution(
                contribution=contribution),
            (await self._request('%s/list?%s' % (ENDPOINTS.CONTRIBUTIONS,
                                                 '&'.join(params)))) or []
        ))

    async def list_funds(self, include_totals: bool = False):
        """List all funds.

        Args:
          include_totals: Amount given to the fund should be returned.

        Returns:
          JSON Reponse."""

        params = []
        if include_totals:
            params.append('include_totals=1')

        return list(map(
            lambda fund: self.return_type_parsers.fund(fund=fund),
            (await self._request('%s/list?%s' %
                                 (ENDPOINTS.FUNDS, '&'.join(params)))) or []
        ))

    async def list_campaigns(self):
        """List of campaigns.

        Returns:
          JSON response."""

        return list(map(
            lambda campaign: self.return_type_parsers.campaign(
                campaign=campaign),
            (await self._request('%s/list_campaigns' % (ENDPOINTS.PLEDGES))) or []
        ))

    async def list_pledges(self, campaign_id: Id):
        """List of pledges within a campaign.

        Args:
          campaign_id: ID number of a campaign.

        Returns:
          JSON response."""

        return list(map(
            lambda pledge: self.return_type_parsers.pledge(
                pledge=pledge),
            (await self._request('%s/list_pledges?campaign_id=%s' % (
                ENDPOINTS.PLEDGES, campaign_id
            ))) or []
        ))

    async def list_forms(self, is_archived: bool = False):
        """List all forms.

        Args:
          is_archived: If set to True, archived forms will be returned instead of active forms.

        Returns:
          JSON Response."""

        params = []
        if is_archived:
            params.append('is_archived=1')

        return list(map(
            lambda form: self.return_type_parsers.form(form=form),
            (await self._request('%s/list_forms?%s' %
                                 (ENDPOINTS.FORMS, '&'.join(params)))) or []
        ))

    async def list_form_fields(self, form_id: Id):
        """List the fields for a given form.

        Args:
          form_id: The fields will be returned that correspond to the form id provided.

        Returns:
          JSON Reponse."""

        params = ['form_id=%s' % form_id]

        return list(map(
            lambda form_field: self.return_type_parsers.form_field(
                form_field=form_field),
            (await self._request('%s/list_form_fields?%s' %
                                 (ENDPOINTS.FORMS, '&'.join(params)))) or []
        ))

    async def list_form_entries(self, form_id: Id, details: bool = True):
        """List all forms entries.

        Args:
          form_id: The entries will be returned that correspond to the numeric form id provided.

          details: If set to True, the entry responses will be returned as well. The entry response array has key values that correspond to the form fields.

        Returns:
          JSON Reponse."""

        params = ['form_id=%s' % form_id]
        if details:
            params.append('details=1')

        return list(map(
            lambda entry: self.return_type_parsers.form_entry(
                entry=entry),
            (await self._request(
                '%s/list_form_entries?%s' %
                (ENDPOINTS.FORMS, '&'.join(params)))) or []
        ))

    async def list_volunteers(self, instance_id: Id):
        """List volunteers from a specific event.

          Args:
            instance_id: The id of the event instance you want to list the volunteers for.

          Returns:
            JSON response."""

        params = ['instance_id=%s' % instance_id, ]

        return list(map(
            lambda volunteer: self.return_type_parsers.volunteer(
                volunteer=volunteer),
            (await self._request('%s/list?%s' %
                                 (ENDPOINTS.VOLUNTEERS, '&'.join(params)))) or []
        ))

    async def list_volunteer_roles(self, instance_id: Id,
                                   show_quantity: bool = True):
        """List volunteers from a specific event.

          Args:
            instance_id: The id of the event instance you want to retrieve the volunteer roles for.
            show_quantity: Option to return quantity requested for each role.

          Returns:
            JSON response."""

        params = ['instance_id=%s' % instance_id, ]
        if show_quantity:
            params.append('show_quantity=1')

        return list(map(
            lambda role: self.return_type_parsers.volunteer_role(role=role),
            (await self._request('%s/list_roles?%s' %
                                 (ENDPOINTS.VOLUNTEERS, '&'.join(params)))) or []
        ))

    async def get_account_summary(self):
        """Retrieve the details for a specific account using the API key
          and URL. It can also work to see if the key and URL are valid.

        Returns:
          JSON response. For example:
          {
            "id":"1234",
            "name":"Grace Church",
            "subdomain":"gracechurchdemo",
            "status":"1",
            "created_on":"2018-09-10 09:19:35",
            "details":{
                "timezone":"America\/New_York",
                "country":{
                    "id":"2",
                    "name":"United States of America",
                    "abbreviation":"USA",
                    "abbreviation_2":"US",
                    "currency":"USD",
                    "currency_symbol":"$",
                    "date_format":"MDY",
                    "sms_prefix":"1"
                }
            }
          }
          """

        account = await self._request(f"{ENDPOINTS.BREEZE_ACCOUNT}/summary")

        if not account:
            return None

        return self.return_type_parsers.breeze_account(account=account)

    async def get_account_log(self,
                              action: AccountLogActions, start_date: datetime = None,
                              end_date: datetime = None,
                              user_id: Id = None,
                              details: bool = False,
                              limit: int = 500):
        """Retrieve a list of events based on search criteria.

        Args:
             action: A required parameter indicating which type of logged action should be returned.

             start_date: The start date range for actions that should be returned. If not provided, logged items will be fetched from as long ago as the log is storing.

             end_date: The end date range for actions that should be returned. If not provided, logged items will be fetched up until the current moment.

             user_id: The user_id of the user who made the logged action. If not provided, all users' actions will be returned.

             details: If details about the logged action should be returned. Note that this column is not guaranteed to be standardized and should not be relied upon for anything more than a description.

             limit: The number of logged items to return. Max is 3,000.

        returns: JSON response."""

        params = [f"action={action.name}"]

        if start_date:
            params.append(
                f"start={type_parsing.date_to_str(start_date, 'YYYY-MM-DD')}")
        if end_date:
            params.append(
                f"end={type_parsing.date_to_str(end_date, 'YYYY-MM-DD')}")
        if user_id:
            params.append(f"user_id={user_id}")
        if limit:
            params.append(f"limit={min(limit, 3000)}")
        if details:
            params.append("details=1")

        return list(map(
            lambda account_log: self.return_type_parsers.breeze_account_log(
                account_log=account_log),
            (await self._request(f"{ENDPOINTS.BREEZE_ACCOUNT}/list_log?{'&'.join(params)}", timeout=180)) or []
        ))

    # write, update, delete

    def add_person(self, first_name, last_name, fields_json=None):
        """Adds a new person into the database.

        Args:
          first_name: The first name of the person.
          last_name: The first name of the person.
          fields_json: JSON string representing an array of fields to update.
                       Each array element must contain field id, field type, response,
                       and in some cases, more information.
                       ie. [{
                               "field_id": "929778337",
                               "field_type": "email",
                               "response": "true",
                               "details": {
                                    "address": "tony@starkindustries.com",
                                    "is_private": 1}
                             }
                           ].
                       Obtain such field information from get_profile_fields() or
                       use get_person_details() to see fields that already exist for a specific person.

        Returns:
          JSON response equivalent to get_person_details()."""

        params = []
        params.append('first=%s' % first_name)
        params.append('last=%s' % last_name)
        if fields_json:
            params.append('fields_json=%s' % fields_json)

        return self._request('%s/add?%s' % (ENDPOINTS.PEOPLE, '&'.join(params)))

    def update_person(self, person_id, fields_json):
        """Updates the details for a specific person in the database.

        Args:
          person_id: Unique id for a person in Breeze database.
          fields_json: JSON string representing an array of fields to update.
                       Each array element must contain field id, field type, response,
                       and in some cases, more information.
                       ie. [{
                               "field_id": "929778337",
                               "field_type": "email",
                               "response": "true",
                               "details": {
                                    "address": "tony@starkindustries.com",
                                    "is_private": 1}
                             }
                           ].
                       Obtain such field information from get_profile_fields() or
                       use get_person_details() to see fields that already exist for a specific person.

        Returns:
          JSON response equivalent to get_person_details(person_id)."""

        return self._request(
            '%s/update?person_id=%s&fields_json=%s' % (
                ENDPOINTS.PEOPLE, person_id, fields_json
            ))

    def event_check_in(self, person_id, event_instance_id):
        """Checks in a person into an event.

        Args:
          person_id: id for a person in Breeze database.
          event_instance_id: id for event instance to check into.."""

        return self._request(
            '%s/attendance/add?person_id=%s&instance_id=%s' % (
                ENDPOINTS.EVENTS, str(person_id), str(event_instance_id)
            ))

    def event_check_out(self, person_id, event_instance_id):
        """Remove the attendance for a person checked into an event.

        Args:
          person_id: Breeze ID for a person in Breeze database.
          event_instance_id: id for event instance to check out(delete).

        Returns:
          True if check-out succeeds; False if check-out fails."""

        return self._request(
            '%s/attendance/delete?person_id=%s&instance_id=%s' % (
                ENDPOINTS.EVENTS, str(person_id), str(event_instance_id)
            ))

    def add_contribution(self,
                         date=None,
                         name=None,
                         person_id=None,
                         uid=None,
                         processor=None,
                         method=None,
                         funds_json=None,
                         amount=None,
                         group=None,
                         batch_number=None,
                         batch_name=None):
        """Add a contribution to Breeze.

        Args:
          date: Date of transaction in DD-MM-YYYY format(ie. 24-5-2015)
          name: Name of person that made the transaction. Used to help match up
                contribution to correct profile within Breeze.  (ie. John Doe)
          person_id: The Breeze ID of the donor. If unknown, use UID instead of
                     person id(ie. 1234567)
          uid: The unique id of the person sent from the giving platform. This
               should be used when the Breeze ID is unknown. Within Breeze a
               user will be able to associate this ID with a given Breeze ID.
               (ie. 9876543)
          email: Email address of donor. If no person_id is provided, used to
                 help automatically match the person to the correct profile.
                 (ie. sample@breezechms.com)
          street_address: Donor's street address. If person_id is not provided,
                          street_address will be used to help automatically
                          match the person to the correct profile.
                          (ie. 123 Sample St)
          processor: The name of the processor used to send the payment. Used
                     in conjunction with uid. Not needed if using Breeze ID.
                     (ie. SimpleGive, BluePay, Stripe)
          method: The payment method. (ie. Check, Cash, Credit/Debit Online,
                  Credit/Debit Offline, Donated Goods(FMV), Stocks(FMV),
                  Direct Deposit)
          funds_json: JSON string containing fund names and amounts. This
                      allows splitting fund giving. The ID is optional. If
                      present, it must match an existing fund ID and it will
                      override the fund name.
                      ie. [{
                              'id': '12345',
                              'name': 'General Fund',
                              'amount': '100.00'
                            },
                            {
                              'name': 'Missions Fund',
                              'amount': '150.00'
                            }
                          ]
          amount: Total amount given. Must match sum of amount in funds_json.
          group: This will create a new batch and enter all contributions with
                 the same group into the new batch. Previous groups will be
                 remembered and so they should be unique for every new batch.
                 Use this if wanting to import into the next batch number in a
                 series.
          batch_number: The batch number to import contributions into. Use
                        group instead if you want to import into the next batch
                        number.
          batch_name: The name of the batch. Can be used with batch number or
                      group.

        Returns:
          Payment Id.

        Throws:
          BreezeError on failure to add contribution."""

        params = []
        if date:
            params.append('date=%s' % date)
        if name:
            params.append('name=%s' % name)
        if person_id:
            params.append('person_id=%s' % person_id)
        if uid:
            params.append('uid=%s' % uid)
        if processor:
            params.append('processor=%s' % processor)
        if method:
            params.append('method=%s' % method)
        if funds_json:
            params.append('funds_json=%s' % funds_json)
        if amount:
            params.append('amount=%s' % amount)
        if group:
            params.append('group=%s' % group)
        if batch_number:
            params.append('batch_number=%s' % batch_number)
        if batch_name:
            params.append('batch_name=%s' % batch_name)
        response = self._request('%s/add?%s' % (ENDPOINTS.CONTRIBUTIONS,
                                                '&'.join(params)))
        return response['payment_id']

    def edit_contribution(self,
                          payment_id=None,
                          date=None,
                          name=None,
                          person_id=None,
                          uid=None,
                          processor=None,
                          method=None,
                          funds_json=None,
                          amount=None,
                          group=None,
                          batch_number=None,
                          batch_name=None):
        """Edit an existing contribution.

        Args:
          payment_id: The ID of the payment that should be modified.
          date: Date of transaction in DD-MM-YYYY format(ie. 24-5-2015)
          name: Name of person that made the transaction. Used to help match up
                contribution to correct profile within Breeze.  (ie. John Doe)
          person_id: The Breeze ID of the donor. If unknown, use UID instead of
                     person id(ie. 1234567)
          uid: The unique id of the person sent from the giving platform. This
               should be used when the Breeze ID is unknown. Within Breeze a
               user will be able to associate this ID with a given Breeze ID.
               (ie. 9876543)
          email: Email address of donor. If no person_id is provided, used to
                 help automatically match the person to the correct profile.
                 (ie. sample@breezechms.com)
          street_address: Donor's street address. If person_id is not provided,
                          street_address will be used to help automatically
                          match the person to the correct profile.
                          (ie. 123 Sample St)
          processor: The name of the processor used to send the payment. Used
                     in conjunction with uid. Not needed if using Breeze ID.
                     (ie. SimpleGive, BluePay, Stripe)
          method: The payment method. (ie. Check, Cash, Credit/Debit Online,
                  Credit/Debit Offline, Donated Goods(FMV), Stocks(FMV),
                  Direct Deposit)
          funds_json: JSON string containing fund names and amounts. This
                      allows splitting fund giving. The ID is optional. If
                      present, it must match an existing fund ID and it will
                      override the fund name.
                      ie. [{
                              'id': '12345',
                              'name': 'General Fund',
                              'amount': '100.00'
                            },
                            {
                              'name': 'Missions Fund',
                              'amount': '150.00'
                            }
                          ]
          amount: Total amount given. Must match sum of amount in funds_json.
          group: This will create a new batch and enter all contributions with
                 the same group into the new batch. Previous groups will be
                 remembered and so they should be unique for every new batch.
                 Use this if wanting to import into the next batch number in a
                 series.
          batch_number: The batch number to import contributions into. Use
                        group instead if you want to import into the next batch
                        number.
          batch_name: The name of the batch. Can be used with batch number or
                      group.

        Returns:
          Payment id.

        Throws:
          BreezeError on failure to edit contribution."""

        params = []
        if payment_id:
            params.append('payment_id=%s' % payment_id)
        if date:
            params.append('date=%s' % date)
        if name:
            params.append('name=%s' % name)
        if person_id:
            params.append('person_id=%s' % person_id)
        if uid:
            params.append('uid=%s' % uid)
        if processor:
            params.append('processor=%s' % processor)
        if method:
            params.append('method=%s' % method)
        if funds_json:
            params.append('funds_json=%s' % funds_json)
        if amount:
            params.append('amount=%s' % amount)
        if group:
            params.append('group=%s' % group)
        if batch_number:
            params.append('batch_number=%s' % batch_number)
        if batch_name:
            params.append('batch_name=%s' % batch_name)
        response = self._request('%s/edit?%s' % (ENDPOINTS.CONTRIBUTIONS,
                                                 '&'.join(params)))
        return response['payment_id']

    def delete_contribution(self, payment_id):
        """Delete an existing contribution.

        Args:
          payment_id: The ID of the payment that should be deleted.

        Returns:
          Payment id.

        Throws:
          BreezeError on failure to delete contribution."""

        response = self._request('%s/delete?payment_id=%s' % (
            ENDPOINTS.CONTRIBUTIONS, payment_id
        ))
        return response['payment_id']

    def remove_form_entry(self, entry_id):
        """Remove Form Entry.

        Args:
          entry_id: The id of the form entry you want to remove.

        Returns:
          JSON Reponse."""

        params = ['entry_id=%s' % entry_id]
        return self._request('%s/remove_form_entry?%s' %
                             (ENDPOINTS.FORMS, '&'.join(params)))

    def add_tag(self, name, folder_id=None):
        """Add a new tag

        Args:
          name: The name of the tag.
          folder_id: The specific folder to place the tag can be specified. If omitted, the tag will be placed in the top level folder.

        Returns: JSON response.
        """
        params = ['name=%s' % name]
        if folder_id:
            params.append('folder_id=%s' % folder_id)

        return self._request('%s/add_tag?%s' % (ENDPOINTS.TAGS,
                                                '&'.join(params)))

    def delete_tag(self, tag_id: Id):
        return self._request(f"{ENDPOINTS.TAGS}/delete_tag?tag_id={tag_id}")

    def assign_tag(self,
                   person_id,
                   tag_id):
        """
        Update a person's tag/s.

        params:

        person_id: an existing person's user id

        tag_id: the id number of the tag you want to assign to the user

        output: true or false upon success or failure of tag update
        """
        params = []

        params.append('person_id=%s' % person_id)

        params.append('tag_id=%s' % tag_id)

        response = self._request('%s/assign?%s' %
                                 (ENDPOINTS.TAGS, '&'.join(params)))

        return response

    def unassign_tag(self,
                     person_id,
                     tag_id):
        """
        Delete a person's tag/s.

        params:

        person_id: an existing person's user id

        tag_id: the id number of the tag you want to assign to the user

        output: true or false upon success or failure of tag deletion
        """
        params = []

        params.append('person_id=%s' % person_id)

        params.append('tag_id=%s' % tag_id)

        response = self._request('%s/unassign?%s' %
                                 (ENDPOINTS.TAGS, '&'.join(params)))

        return response

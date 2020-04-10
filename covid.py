from collections import defaultdict
from enum import Enum
from typing import Dict, List, Optional

import requests
import rumps


class StatisticsTimeType(Enum):
    today = "Today"
    total = "Total"


class StatisticsEventType(Enum):
    confirmed = "Confirmed"
    deaths = "Deaths"
    recovered = "Recovered"
    active = "Active"


class About(rumps.Window):
    def __init__(self):
        super().__init__(title="About")
        self.default_text = "Version: 0.0.1\nAuthor: https://tobked.github.io/"


class Country:
    COUNTRY_STATUS_FMT = "https://api.covid19api.com/live/country/%s/status/confirmed"

    def __init__(self, country: str, slug: str, iso2: str) -> None:
        self.country = country
        self.slug = slug
        self.iso2 = iso2

    def __str__(self):
        return self.country

    def get_statistics(self) -> Dict[str, Dict[str, str]]:
        data = defaultdict(dict)
        url = self.COUNTRY_STATUS_FMT % self.slug
        response = requests.get(url)
        response.raise_for_status()
        json_data = response.json()

        for _, key in StatisticsEventType.__members__.items():
            data[StatisticsTimeType.total.name][key.name] = json_data[-1][key.value]
            data[StatisticsTimeType.today.name][key.name] = (
                json_data[-1][key.value] - json_data[-2][key.value]
            )
        return data


class CountryMenuItem(rumps.MenuItem):
    def __init__(self, *args, **kwargs):
        country = dict()
        if "country" in kwargs:
            country = kwargs.pop("country")

        super().__init__(*args, **kwargs)
        self.country = country


class EventTypeMenuItem(rumps.MenuItem):
    def __init__(self, *args, **kwargs):
        event_type = None
        if "event_type" in kwargs:
            event_type = kwargs.pop("event_type")

        super().__init__(*args, **kwargs)
        self.event_type = event_type


class AwesomeStatusBarApp(rumps.App):
    APP_NAME = "Covid"
    DEFAULT_COUNTRY = Country("Poland", "poland", "PL")
    DEFAULT_STATISTICS_EVENT_TYPE = StatisticsEventType.deaths
    DEFAULT_STATISTICS_TIME_TYPE = StatisticsTimeType.total
    COUNTRIES_URL = "https://api.covid19api.com/countries"

    def __init__(self):
        super().__init__(self.APP_NAME)
        self._countries_list: Optional[List[Dict[str, str]]] = None
        self._selected_country: Country = self.DEFAULT_COUNTRY
        self._selected_statistics_event_type = self.DEFAULT_STATISTICS_EVENT_TYPE
        self._selected_statistics_time_type = self.DEFAULT_STATISTICS_TIME_TYPE

        self.menu_countries = rumps.MenuItem(title="Country")
        self.update_countries_selection()

        self.menu_event_types = rumps.MenuItem(title="Event type")
        self.update_event_type_selection()

        self.menu = [self.menu_event_types, self.menu_countries]

    @property
    def countries_list(self) -> List[Country]:
        if self._countries_list is None:
            self._countries_list = self.__get_countries()
        return self._countries_list

    def update_countries_selection(self) -> None:
        for country in self.countries_list:
            if country.country in self.menu_countries:
                self.menu_countries[country.country].state = (
                    1 if country == self._selected_country else 0
                )
                continue
            menu_item = CountryMenuItem(
                title="%s" % country.country,
                callback=self.menu_country_item_callback,
                country=country,
            )
            menu_item.state = 1 if country == self._selected_country else 0
            self.menu_countries.add(menu_item)

    def __get_countries(self) -> List[Country]:
        response = requests.get(self.COUNTRIES_URL)
        response.raise_for_status()
        json_data = response.json()
        return [
            Country(data["Country"], data["Slug"], data["ISO2"])
            for data in sorted(json_data, key=lambda x: x["Country"])
        ]

    @rumps.clicked("About")
    def about(self, _) -> None:
        About().run()

    def menu_country_item_callback(
        self, single_country_menu_item: CountryMenuItem
    ) -> None:
        self._selected_country = single_country_menu_item.country
        self.update_countries_selection()
        self.update_data()

    def update_data(self):
        statistics = self._selected_country.get_statistics()
        deaths_today = statistics[self._selected_statistics_time_type.name][
            self._selected_statistics_event_type.name
        ]
        self._update_title(
            value=deaths_today,
            time_type=self._selected_statistics_time_type.name,
            event_type=self._selected_statistics_event_type.name,
        )

    def _update_title(self, value: str, time_type: str, event_type: str) -> None:
        self.title = f"{self.APP_NAME} - {event_type} {time_type} in {self._selected_country.country}: {value}"

    def update_event_type_selection(self) -> None:
        for _, event_type in StatisticsEventType.__members__.items():
            if event_type.value in self.menu_event_types:
                self.menu_event_types[event_type.value].state = (
                    1 if event_type == self._selected_statistics_event_type else 0
                )
                continue
            menu_item = EventTypeMenuItem(
                title="%s" % event_type.value,
                callback=self.menu_event_item_callback,
                event_type=event_type,
            )
            menu_item.state = (
                1 if event_type == self._selected_statistics_event_type else 0
            )
            self.menu_event_types.add(menu_item)

    def menu_event_item_callback(
        self, single_event_menu_item: EventTypeMenuItem
    ) -> None:
        self._selected_statistics_event_type = single_event_menu_item.event_type
        self.update_event_type_selection()
        self.update_data()

    @rumps.timer(600)
    def update(self, _) -> None:
        self.update_data()


if __name__ == "__main__":
    AwesomeStatusBarApp().run()

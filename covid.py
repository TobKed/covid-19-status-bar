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


class AwesomeStatusBarApp(rumps.App):
    APP_NAME = "Covid"
    DEFAULT_COUNTRY = Country("Poland", "poland", "PL")
    COUNTRIES_URL = "https://api.covid19api.com/countries"

    def __init__(self):
        super().__init__(self.APP_NAME)
        self._countries_list: Optional[List[Dict[str, str]]] = None
        self._selected_country: Country = self.DEFAULT_COUNTRY

        self.menu_countries = rumps.MenuItem(title="Country")
        self.update_countries_selection()

        self.menu = [self.menu_countries]

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
                callback=self.menu_item_callback,
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

    def menu_item_callback(self, single_country_menu_item: CountryMenuItem) -> None:
        self._selected_country = single_country_menu_item.country
        self.update_countries_selection()
        self.update_data()

    def update_data(self):
        statistics = self._selected_country.get_statistics()
        deaths_today = statistics[StatisticsTimeType.today.name][
            StatisticsEventType.deaths.name
        ]
        self._update_title(
            value=deaths_today,
            time_type=StatisticsTimeType.today.name,
            event_type=StatisticsEventType.deaths.name,
        )

    def _update_title(
        self,
        value: str,
        time_type: Optional[str] = StatisticsTimeType.today.name,
        event_type: Optional[str] = StatisticsEventType.deaths.name,
    ) -> None:
        self.title = f"{self.APP_NAME} - {event_type} {time_type} in {self._selected_country.country}: {value}"

    @rumps.timer(600)
    def update(self, _) -> None:
        self.update_data()


if __name__ == "__main__":
    AwesomeStatusBarApp().run()

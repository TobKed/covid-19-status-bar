from enum import Enum
from typing import Any, Dict, List, Optional, Union

import requests
import rumps


class EventType(Enum):
    cases = "cases"
    todayCases = "today cases"
    deaths = "deaths"
    todayDeaths = "today deaths"
    recovered = "recovered"
    active = "active"
    critical = "critical"
    casesPerOneMillion = "cases per one million"
    deathsPerOneMillion = "deaths per one million"
    tests = "tests"
    testsPerOneMillion = "tests per one million"


class About(rumps.Window):
    def __init__(self):
        super().__init__(title="About")
        self.default_text = "Version: 0.0.1\nAuthor: https://tobked.github.io/"


class CountryMenuItem(rumps.MenuItem):
    def __init__(self, *args, **kwargs):
        country = dict()
        if "country" in kwargs:
            country = kwargs.pop("country")

        super().__init__(*args, **kwargs)
        self.country = country


class EventTypeMenuItem(rumps.MenuItem):
    def __init__(self, *args, **kwargs):
        event_type = kwargs.pop("event_type")
        super().__init__(*args, **kwargs)
        self.event_type = event_type


class Covid19StatusBarApp(rumps.App):
    APP_NAME = "Covid-19"
    BASE_API_URL = "https://corona.lmao.ninja"
    DEFAULT_COUNTRY = "Poland"

    def __init__(self):
        super().__init__(self.APP_NAME)
        self._countries_list: Optional[List[str]] = None
        self._selected_country: str = self.DEFAULT_COUNTRY
        self._selected_event_type: EventType = EventType.active

        self.menu_countries = rumps.MenuItem(title="Country")
        self.update_countries_selection()

        self.menu_event_types = rumps.MenuItem(title="Event type")
        self.update_event_type_selection()

        self.update_data()

        self.menu = [self.menu_countries, self.menu_event_types]

    def __get_countries(self) -> List[str]:
        response = requests.get(f"{self.BASE_API_URL}/countries")
        return sorted([e["country"] for e in response.json()])

    def get_country_data(self, country: str) -> Dict[str, Any]:
        response = requests.get(f"{self.BASE_API_URL}/countries/{country}")
        return response.json()

    @property
    def countries_list(self) -> List[str]:
        if self._countries_list is None:
            self._countries_list = self.__get_countries()
        return self._countries_list

    def update_countries_selection(self) -> None:
        for country in self.countries_list:
            if country in self.menu_countries:
                self.menu_countries[country].state = (
                    1 if country == self._selected_country else 0
                )
                continue
            menu_item = rumps.MenuItem(
                title=country, callback=self.menu_country_item_callback,
            )
            menu_item.state = 1 if country == self._selected_country else 0
            self.menu_countries.add(menu_item)

    def menu_country_item_callback(
        self, single_country_menu_item: CountryMenuItem
    ) -> None:
        self._selected_country = single_country_menu_item.title
        self.update_countries_selection()
        self.update_data()

    def update_data(self):
        self._data = self.get_country_data(self._selected_country)
        self._update_title(
            value=self._data[self._selected_event_type.name],
            event_type=self._selected_event_type.value,
        )

    def _update_title(self, value: Union[str, int], event_type: str) -> None:
        self.title = (
            f"{self.APP_NAME} - {event_type} in {self._selected_country}: {value}"
        )

    def update_event_type_selection(self) -> None:
        for _, event_type in EventType.__members__.items():
            if event_type.value in self.menu_event_types:
                self.menu_event_types[event_type.value].state = (
                    1 if event_type == self._selected_event_type else 0
                )
                continue
            menu_item = EventTypeMenuItem(
                title="%s" % event_type.value,
                callback=self.menu_event_type_item_callback,
                event_type=event_type,
            )
            menu_item.state = 1 if event_type == self._selected_event_type else 0
            self.menu_event_types.add(menu_item)

    def menu_event_type_item_callback(
        self, single_event_menu_item: EventTypeMenuItem
    ) -> None:
        self._selected_event_type = single_event_menu_item.event_type
        self.update_event_type_selection()
        self.update_data()

    @rumps.timer(600)
    def update(self, _) -> None:
        self.update_data()

    @rumps.clicked("About")
    def about(self, _) -> None:
        About().run()


if __name__ == "__main__":
    Covid19StatusBarApp().run()

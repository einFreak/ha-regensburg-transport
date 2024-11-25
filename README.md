[![version](https://img.shields.io/github/manifest-json/v/einFreak/ha-regensburg-transport?filename=custom_components%2Fregensburg_transport%2Fmanifest.json&color=slateblue)](https://github.com/einFreak/ha-regensburg-transport/releases/latest)
![GitHub all releases](https://img.shields.io/github/downloads/einFreak/ha-regensburg-transport/total)
[![HACS](https://img.shields.io/badge/HACS-Default-orange.svg?logo=HomeAssistantCommunityStore&logoColor=white)](https://github.com/hacs/integration)
[![Ko-Fi](https://img.shields.io/static/v1.svg?label=%20&message=Ko-Fi&color=F16061&logo=ko-fi&logoColor=white)](https://www.ko-fi.com/einfreak)
[![PayPal.Me](https://img.shields.io/static/v1.svg?label=%20&message=PayPal.Me&logo=paypal)](https://paypal.me/einfreak)

# Regensburg (RVV) transport sensor for Home Assistant

Custom sensor component that displays upcoming departures from your defined public transport stops for Regensburg (and RVV area).


## 💿 Installation

The component consists of a sensor, which tracks departures via RVV Public API every 120 seconds

We will look at the installation of each of them separately below. But first, let's learn how to find the Stop IDs.

### Install sensor component

**1.** Copy the whole [regensburg_transport](./custom_components/) directory to the `custom_components` folder of your Home Assistant installation. If you can't find the `custom_components` directory at the same level with your `configuration.yml` — simply create it yourself and put `dresden_transport` there.

**2.** Go to Home Assistant web interface -> `Developer Tools` -> `Check and Restart` and click "Restart" button. It will reload all components in the system.

**3.** Now you can add your new custom sensor by adding the newly added Regensburg Transport Integration and following the config flow

## 🚨 Update
This update brings new sensor id generation. It will result in deactivation of sensors with the old ids. All of those inactive sensors can be manually deleted either from the lovelace card directly and refreshing the dashboard or from the entities list in `Settings`.

## 👩‍💻 Technical details

This sensor uses RVV Public API to fetch all transport information.

The component updates every 120 seconds, but it makes a separate request for each stop.

After fetching the API, it creates one entity for each stop and writes 5 upcoming departures into `attributes.departures`. The entity state is not really used anywhere, it just shows the next departure in a human-readable format. If you have any ideas how to use it better — welcome to Github Issues.

## ❤️ Contributions

Contributions are welcome. Feel free to [open a PR](https://github.com/einfreak/ha-regensburg-transport/pulls) and send it to review. If you are unsure, [open an Issue](https://github.com/einfreak/ha-regensburg-transport/issues) and ask for advice.

## 🐛 Bug reports and feature requests

Since this is my small hobby project, I cannot guarantee you a 100% support or any help with configuring your dashboards. I hope for your understanding.

- **If you find a bug** - open [an Issue](https://github.com/einfreak/ha-regensburg-transport/issues) and describe the exact steps to reproduce it. Attach screenshots, copy all logs and other details to help me find the problem.

## Credits

This module is a fork of [vas3k repo](https://github.com/vas3k/home-assistant-berlin-transport) made for Berlin and [VDenisyuk repo](https://github.com/VDenisyuk/home-assistant-transport) for Dresden.

## 👮‍♀️ License

- [MIT](./LICENSE.md)


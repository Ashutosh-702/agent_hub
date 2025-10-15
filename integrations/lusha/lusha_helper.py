from typing import Dict, Any, List, OrderedDict

from structlog.contextvars import bind_contextvars

from integrations.config.constants import MAX_EMPLOYEES, DOLLAR_TO_INR_RATIO, MILLION_TO_ACTUAL
from integrations.config.lusha_industry_config import LUSHA_CONFIG
from integrations.config.country_api_results import LUSHA_COUNTRY_CONFIG
from integrations.lusha.lusha_api import LushaAPIClient
from config.logging import logger


class LushaHelper:
    def __init__(self):
        self.LUSHA_LOOKUP = {}
        self._load_config()

    def _load_config(self):
        for main in LUSHA_CONFIG:
            for sub in main.sub_industries:
                self.LUSHA_LOOKUP[sub.value] = sub.id

    def get_industry_mapping(self) -> Dict[str, int]:
        """
        Fetch industry name to ID mapping from Google Sheets
        Returns: Dictionary mapping industry names to Lusha industry IDs
        """
        try:
            mapping = {"Sub": {}, "Main": {}}

            for name, id_val in self.LUSHA_LOOKUP.items():
                mapping["Sub"][name] = id_val

            return mapping

        except Exception as e:
            logger.info(f"❌ Error loading industry mapping: {e}")

            return {}

    def parse_employee_range(self, range_str: str) -> tuple:
        """
        Parse employee range strings like '11-50', '201+' to min/max values
        """
        range_str = range_str.strip()

        if '+' in range_str:
            min_val = int(range_str.replace('+', ''))
            return min_val, MAX_EMPLOYEES

        elif '-' in range_str:
            parts = range_str.split('-')

            if len(parts) == 2:
                return int(parts[0]), int(parts[1])

        try:
            val = int(range_str)
            return val, val

        except:
            return 1, 10

    def convert_revenue_to_actual(self, revenue_millions: str, currency: str = "USD") -> int:
        """
        Convert revenue from millions to actual numbers
        """
        # if curency is INR then conert to usd

        try:
            if currency == "INR":
                revenue_millions = float(revenue_millions) / DOLLAR_TO_INR_RATIO

            revenue_float = float(revenue_millions)
            actual = int(revenue_float * MILLION_TO_ACTUAL)
            # TODO: Currency conversion logic

            return actual
        except:
            return 0

    def sheets_to_lusha_config(self, sheets_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert sheets configuration to Lusha API configuration
        """
        lusha_config = {
            "pages": {"page": 0, "size": 40}
        }
        industry_names = sheets_data.get("segmentation", {}).get("industry", [])

        if not isinstance(industry_names, list):
            logger.info(f"⚠️ Expected list for industry names, got: {type(industry_names)}")
            industry_names = []

        sub_ids = []
        
        for name in industry_names:
            if name in self.LUSHA_LOOKUP:
                sub_ids.append(self.LUSHA_LOOKUP[name])
            else:
                logger.info(f"⚠️ Industry '{name}' not found in mapping")
                
        if sub_ids:
            lusha_config["subIndustriesIds"] = list(OrderedDict.fromkeys(sub_ids))

        if sheets_data.get("target", {}).get("location", {}).get("names"):
            lusha_locations = []
            location_type = sheets_data['target']["location"]['type']
            locations = sheets_data['target']["location"]['names']
            
            for location in locations:
                if location in LUSHA_COUNTRY_CONFIG:
                    lusha_locations.append(
                        LUSHA_COUNTRY_CONFIG[location].get(
                            "country", location)
                    )

                else:
                    lusha_locations.append(location)

            if lusha_locations:
                    lusha_config["locations"] = lusha_locations
                    lusha_config["location_type"] = location_type

        revenue_min = sheets_data.get("target", "")['revenue_min']
        revenue_max = sheets_data.get("target", "")['revenue_max']
        currency = sheets_data.get("target", "")['currency']

        logger.info(f"revenue_min_check: {revenue_min}, revenue_max_check: {revenue_max}, currency: {currency}")
        # here value is coming in this way
        # revenue_min_check: (1,), revenue_max_check: (2,), currency: ('USD',)
        
        if revenue_min and revenue_max:
            try:
                min_value = self._clean_tuple_value(revenue_min) 
                max_value = self._clean_tuple_value(revenue_max) 
                currency_value = self._clean_tuple_value(currency) 
                min_actual = self.convert_revenue_to_actual(min_value, currency_value)
                max_actual = self.convert_revenue_to_actual(max_value, currency_value)
                logger.info(f"min_actual: {min_actual}, max_actual: {max_actual}")

                if min_actual > 0 or max_actual > 0:
                    lusha_config["revenue"] = {
                        "min": min_actual if min_actual > 0 else 1,
                        "max": max_actual
                    }

            except Exception as e:
                logger.info(f"⚠️ Error processing revenue: {e}")

        if sheets_data.get("target", "")['employee_count']:
            employee_ranges = [
                range_str for range_str in sheets_data['target']["employee_count"] if range_str]

            if employee_ranges and employee_ranges[0] != "null":
                logger.info(f"employee_ranges: {employee_ranges}")
                sizes = []

                for range in employee_ranges:
                    logger.info(f"range_value: {range}")
                    min_emp, max_emp = self.parse_employee_range(range)
                    sizes.append({
                        "min": min_emp,
                        "max": max_emp
                    })

                logger.info(f"sizes: {sizes}")
                lusha_config["sizes"] = sizes

        lusha_config["campaign_id"] = sheets_data.get("_id")
        logger.info(f"✅ Converted sheets config to Lusha config: {lusha_config}")

        return lusha_config

    async def get_companies_from_lusha(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Main function to get companies from Lusha using sheets data
        """
        bind_contextvars(operation="get_companies_from_lusha", component="lusha_helper", event_type="lusha_company_search")
        lusha_config = self.sheets_to_lusha_config(config)
        logger.info(f"Lusha config: {lusha_config}")

        if not lusha_config or len(lusha_config) <= 1:
            logger.warning("❌ No valid Lusha configuration generated")
            return []

        try:
            lusha_api_client = LushaAPIClient()
            companies = await lusha_api_client.lusha_collect_companies_from_search(lusha_config, config)
            logger.info(f"✅ Retrieved {companies} companies from Lusha")
            return companies

        except Exception as e:
            logger.error(f"❌ Error calling Lusha API: {e}")
            return []

    def _clean_tuple_value(self, value):
        if value and isinstance(value, tuple) and len(value) > 0:
            return value[0]
            
        return value

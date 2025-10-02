import pytz
from datetime import datetime

class DateTZConverter:
    @staticmethod
    def iso_to_date(date_str):
        """
        Extrai apenas a data (YYYY-MM-DD) de uma string ISO (ex: 2025-08-11T03:00:00:000Z).
        """
        try:
            # Remove milissegundos e 'Z' se existirem
            clean_str = date_str.split('T')[0]
            return clean_str
        except Exception:
            return date_str
        
    @staticmethod
    def to_timezone(date_str, from_tz='UTC', to_tz='America/Sao_Paulo', fmt='%Y-%m-%dT%H:%M:%S'):
        """
        Converte uma string de data entre timezones.
        :param date_str: Data em string (ex: '2025-08-19T15:00:00')
        :param from_tz: Timezone de origem
        :param to_tz: Timezone de destino
        :param fmt: Formato da data
        :return: Data convertida como string no mesmo formato
        """
        from_zone = pytz.timezone(from_tz)
        to_zone = pytz.timezone(to_tz)
        dt = datetime.strptime(date_str, fmt)
        dt = from_zone.localize(dt)
        dt_converted = dt.astimezone(to_zone)
        return dt_converted.strftime(fmt)

    @staticmethod
    def to_utc(date_str, tz='America/Sao_Paulo', fmt='%Y-%m-%dT%H:%M:%S'):
        """
        Converte uma string de data de um timezone para UTC.
        """
        local_zone = pytz.timezone(tz)
        dt = datetime.strptime(date_str, fmt)
        dt = local_zone.localize(dt)
        dt_utc = dt.astimezone(pytz.UTC)
        return dt_utc.strftime(fmt)

    @staticmethod
    def from_utc(date_str, to_tz='America/Sao_Paulo', fmt='%Y-%m-%dT%H:%M:%S'):
        """
        Converte uma string de data de UTC para outro timezone.
        """
        utc_zone = pytz.UTC
        to_zone = pytz.timezone(to_tz)
        dt = datetime.strptime(date_str, fmt)
        dt = utc_zone.localize(dt)
        dt_converted = dt.astimezone(to_zone)
        return dt_converted.strftime(fmt)

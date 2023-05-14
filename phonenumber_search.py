import phonenumbers
from phonenumbers import geocoder, carrier, timezone


def number_lookup(number):
    country_code = '+91'
    # number = '9433964534'
    try:
        if len(str(number)) == 10:

            full_number = country_code + str(number)
            parsed_num = phonenumbers.parse(full_number)

            time_zone = timezone.time_zones_for_number(parsed_num)
            carrier_name = carrier.name_for_number(parsed_num, 'en')
            country_name = geocoder.country_name_for_number(parsed_num, 'en')

            # print(carrier_name)
            # print('i am in try')
            return {'Phone Number': full_number, 'Carrier': carrier_name, 'Time Zone': time_zone[0],
                    'Country Name': country_name}
        else:
            # print('more than 10 digit')
            return {'Error:  ': '   Phone number should be 10 digit long'}
    except phonenumbers.NumberParseException:
        # print(phonenumbers.NumberParseException)
        return {'Error  : ': '   Phone number entered is not valid'}

# print('Phone Number: ' + country_code + ' ' + number)
# print('Timezone: ' + time_zone[0])
# print('Carrier: ', carrier_name)
# print('Country: ', country_name)


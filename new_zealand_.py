import asyncio
import csv
import json

from playwright.async_api import async_playwright
import os

from config import bot_manual_setting, preview
from manage_json import load_json, save_json


async def upload_files(page):
    """Uploads all the required files."""

    async def upload_file(file_input_id, file_path):
        """Uploads a file to the specified file input element."""
        # Set the file input element to the file path
        await page.set_input_files(f"#{file_input_id}", file_path)

    # Upload Passport Style Photograph
    await upload_file("QUploadFacialImage", "/path/to/passport_photo.jpg")

    # Upload Passport Pages
    await upload_file("QUploadPassport", "/path/to/passport_pages.pdf")

    # Upload Offer of Place
    await upload_file("QUploadOfferOfPlace", "/path/to/offer_of_place.pdf")

    # Upload Evidence of Fees Exemption
    await upload_file("QUploadFeesExempt", "/path/to/fees_exemption.pdf")

    # Upload Financial Undertaking
    await upload_file("QUploadFinancialUndertaking", "/path/to/financial_undertaking.pdf")

    # Upload Financial Undertaking Translation
    await upload_file("QUploadFinancialUndertakingTrans", "/path/to/financial_undertaking_translation.pdf")

    # Upload Pre-purchased Travel
    await upload_file("QUploadPrepurchasedTravel", "/path/to/prepurchased_travel.pdf")


################################################


async def fill_contact_form(page, data):
    # Telephone (landline)
    await page.type("#TelephoneLandline_cc", data["TelephoneLandline_cc"])
    await asyncio.sleep(2)
    await page.type("#TelephoneLandline_ac", data["TelephoneLandline_ac"])
    await asyncio.sleep(2)
    await page.type("#TelephoneLandline_num", data["TelephoneLandline_num"])
    await asyncio.sleep(2)

    # Mobile number
    await page.fill("#MobileNumber_cc", data["MobileNumber_cc"])
    await asyncio.sleep(2)
    await page.type("#MobileNumber_num", data["MobileNumber_num"])
    await asyncio.sleep(2)
    await page.fill("#MobileNumber_cc", data["MobileNumber_cc"])

    # Email
    await page.type("#QAppEmailAddr", data["QAppEmailAddr"])
    await asyncio.sleep(2)

    # Confirm email
    await page.type("#QConfirmappEmailAddr", data["QConfirmappEmailAddr"])
    await asyncio.sleep(2)

    # Choose "Yes" or "No" for postal address same as residential address
    same_address = "1" if data["QSameCurrentAddr_1"].lower() == "yes" else "2"
    await page.click(f"#QSameCurrentAddr_{same_address}")
    await asyncio.sleep(2)

    # Choose "Yes" or "No" for being in the same country as residential address
    same_country = "1" if data["QCurrentLocation_1"].lower() == "yes" else "2"
    await page.click(f"#QCurrentLocation_{same_country}")
    await asyncio.sleep(2)


async def select_group_and_agree(page, data):
    # Choose "Yes" or "No" for group application
    group_application = "1" if data["QApplyingForGroup_2"].lower() == "yes" else "2"
    await page.click(f"#QApplyingForGroup_{group_application}")
    await asyncio.sleep(2)

    # # Click the "I agree" checkbox
    # agree_terms = "1" if data["QDeclaration"].lower() == "yes" else "2"
    # await page.click(f"#QDeclaration_{agree_terms}")
    # await asyncio.sleep(4)

    # Click the "I agree" checkbox
    await page.click("#QDeclaration")
    await asyncio.sleep(4)


# def transform_data(data):
#     transformed_data ={}
#     for rows in data:
#         transformed_data[rows[0]] = rows[-1]
#         # transformed_data = {row[0]: row[-1] for row in rows}
#     return transformed_data

def transform_data(data):
    transformed_data = {}
    for row in data:
        if len(row)>4:
            row = row[:4]
            transformed_data[row[0]] = row[-1]

        elif len(row)>=2:
            transformed_data[row[0]] = row[-1]

        # elif len(row) ==4:
        #     transformed_data[row[0]] = row[-2]
        else:
            print(f"Ignoring row: {row}. Insufficient data.")
    return transformed_data


async def is_next_page(update, bot, page=None, mode=None):
    if bot_manual_setting:
        # await update.edit_text("Do you want to continue to next page? Reply with 'Yes' or 'No'")
        recent_message = await bot.message.reply_text("Do you want to continue to next page? Reply with 'Yes' or 'No'",
                                                      reply_to_message_id=bot.message.message_id)

        while True:
            state = load_json()  # Load JSON data inside the loop to get the most recent state
            if state.get("user_confirmed"):
                new_data = {"user_confirmed": False}
                save_json(new_data)

                # Click and go to next page
                await update.edit_text("Clicking Next button.........")
                if mode == 'login':
                    await page.click("button#next")
                    # Check if we have a pop up
                    await check_pop_up(page, bot, index='4', button='button#next')  # First we check if there is error mesage

                    await page.wait_for_load_state(state='domcontentloaded')


                else:
                    await page.click("button.next")
                                # Check if we have a pop up
                    await check_pop_up(page, bot, index='4', button='button.next')  # First we check if there is error mesage

                # await asyncio.sleep(0.5)
                await page.wait_for_load_state(state='domcontentloaded')

                break  # Exit the loop if user_confirmed is True

            await asyncio.sleep(1)
            # print("Waiting for feedback:", state)

        return recent_message

    else:
        # Click and go to next page
        await update.edit_text("Clicking Next button.........")

        if mode == 'login':
            await page.click("button#next")
            # Check if we have a pop up
            await check_pop_up(page, bot, index='4', button='button#next')  # First we check if there is error mesage

        else:
            await page.click("button.next")

            # Check if we have a pop up
            await check_pop_up(page, bot, index='4', button='button.next')  # First we check if there is error mesage
        # await asyncio.sleep(0.5)
        await page.wait_for_load_state(state='domcontentloaded')


async def is_error_page(update, bot, message=None):
    print("error Detected")
    # if bot_manual_setting:
    # await update.edit_text("Do you want to continue to next page? Reply with 'Yes' or 'No'")
    recent_message = await bot.message.reply_text(
        f"‼️The following errors have occurred:\n\n{message}\n\nPlease Reply with 'Yes' or 'No' once you are done to proceed",
        reply_to_message_id=bot.message.message_id)

    while True:
        state = load_json()  # Load JSON data inside the loop to get the most recent state
        if state.get("user_confirmed"):
            new_data = {"user_confirmed": False}
            save_json(new_data)

            break  # Exit the loop if user_confirmed is True

        await asyncio.sleep(1)
        # print("Waiting for feedback:", state)
    return recent_message


async def download_pdf_preview(page, bot, index=''):
    try:
        if int(index) == 10:
            # Wait for the download to complete
            async with page.expect_download() as download_info:
                await page.click('input[type="submit"][value="PDF Preview"]')
                try:
                    # Check if we have a pop up
                    await check_pop_up(page, bot, index='4')  # we will quickly cehck if there is pop up

                    await page.click('input[type="submit"][value="PDF Preview"]')  # click the pdf again after 3 secs
                except:
                    pass


                download = await download_info.value
                print(download)

            # Specify the destination path for the downloaded file
            destination_path = 'download/visa_form_preview.pdf'

            # Move the downloaded file to the desired location with the correct extension
            await download.save_as(destination_path)

            # Send the renamed file to Telegram
            with open(destination_path, 'rb') as file:
                await bot.message.reply_document(document=file, caption=f"Page{index}")

        else:
            return
    except Exception as e:
        print(e)


# async def check_error_message(page):
#     error_message_exists = await page.query_selector('div.validation-errors span[link-to-error="PersonalDetails"]')
#
#     return error_message_exists is not None
async def check_error_message(page):
    # Check if any error message exists
    error_message_exists = await page.query_selector('div.validation-errors')

    # If an error message exists
    if error_message_exists:
        return True

    # If no error message is found, return False
    return False


async def get_error_message(page):
    # Check if any error message exists
    error_message_element = await page.query_selector('div.validation-errors')

    # If an error message exists
    if error_message_element:
        # Get the inner text of the error message element
        error_message = await error_message_element.inner_text()
        return error_message.strip()  # Remove leading and trailing whitespaces

    # If no error message is found, return None
    return None


async def check_pop_up(page, update=None, bot=None, button=None, index=''):
    # wait for at least 5 secs
    try:
        await delay(3)
        popup_exists = await page.query_selector('#popup_container')
        if popup_exists:
            # Click the "OK" button
            await page.click('#popup_ok')

            await delay(3)
            await page.click(button)

        return popup_exists is not None
    except:
        pass

        # await page.click('input[type="submit"][value="PDF Preview"]') # click the pdf again after 3 secs

        # await update.edit_text("Downloading pdf.....")
        # await download_pdf_preview(page, bot, index)




async def handle_next_button(page, update, bot):

    while True:
        is_error = await check_error_message(page)
        if is_error:

            # Get error Message
            error_message = await get_error_message(page)
            print("Error Message ", error_message)
            recent_message = await is_error_page(update, bot, message=error_message)
            # check error message
            await page.click("button.next")
            await page.wait_for_load_state(state='domcontentloaded')


        else:
            break


async def delay(seconds=0.5):
    await asyncio.sleep(seconds)


async def first_page(update, page, data):
    await update.edit_text("Logging in.........")
    await page.fill("#signInName", data.get("signInName", ""))
    await asyncio.sleep(1)
    await page.fill("#password", data.get("password", ""))
    await asyncio.sleep(1)


async def second_page(update, page, data):
    # Click "Yes" or "No" for "Are you applying for a student visa?"
    await asyncio.sleep(5)
    await page.wait_for_selector("#SCStudentVisa_1")
    await update.edit_text("Clicking student visa option.........")

    student_visa_option = "1" if data["SCStudentVisa"].lower() == "yes" else "2"

    await page.click(f"#SCStudentVisa_{student_visa_option}")
    await asyncio.sleep(0.1)

    # Click "Yes" or "No" for "Do you have a MasterCard, Visa or UnionPay card to pay for this application?"
    await update.edit_text("Clicking credit card option.........")
    credit_card_option = "1" if data["SCCreditCard"].lower() == "yes" else "2"
    await page.click(f"#SCCreditCard_{credit_card_option}")
    await asyncio.sleep(0.1)

    # Click "Yes" or "No" for "Are you applying for a student visa as a dependent child of a New Zealand visa holder or applicant?"
    await update.edit_text("Clicking group app option.........")
    group_app_option = "1" if data["SCGroupApp"].lower() == "yes" else "2"
    await page.click(f"#SCGroupApp_{group_app_option}")
    await asyncio.sleep(0.1)

    # Click "Yes" or "No" for "Are you an Australian citizen or permanent resident?"
    await update.edit_text("Clicking Australian option.........")
    australian_option = "1" if data["SCAustralian"].lower() == "yes" else "2"
    await page.click(f"#SCAustralian_{australian_option}")
    await asyncio.sleep(0.1)

    # Click "Yes" or "No" for "Have you claimed refugee or protection status in New Zealand?"
    await update.edit_text("Clicking refugee option.........")
    refugee_option = "1" if data["SCRefugee"].lower() == "yes" else "2"
    await page.click(f"#SCRefugee_{refugee_option}")
    await asyncio.sleep(0.1)

    # Click "Yes" or "No" for "Are you applying under a special Vocational Trainees category?"
    await update.edit_text("Clicking vocational trainee option.........")
    vocational_trainee_option = "1" if data["SCVocationalTrainee"].lower() == "yes" else "2"
    await page.click(f"#SCVocationalTrainee_{vocational_trainee_option}")
    await asyncio.sleep(0.1)

    await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
    await asyncio.sleep(6)
    pass


async def third_page(update, page, data):
    # Fill in personal information
    await update.edit_text("Filling personal information.........")
    await page.type("#QFamilyName", data["QFamilyName"])
    await page.type("#QFirstName", data["QFirstName"])
    await page.type("#QMiddleName", data["QMiddleName"])

    # Select title
    await page.select_option("#Qtitle", label=data["Qtitle"])

    # Fill in additional other names section
    await page.fill("#OtherNames-0-QFamilyNameOther", data["OtherNames-0-QFamilyNameOther"])
    await asyncio.sleep(3)
    await page.fill("#OtherNames-0-QFirstNameOther", data["OtherNames-0-QFirstNameOther"])
    await asyncio.sleep(3)
    await page.fill("#OtherNames-0-QMiddleNameOther", data["OtherNames-0-QMiddleNameOther"])
    await asyncio.sleep(3)
    await page.select_option("#OtherNames-0-NameType", label=data["OtherNames-0-NameType"])

    await asyncio.sleep(1)

    # Select gender
    await update.edit_text("Selecting gender.........")
    gender_option = "1" if data["QGender"].lower() == "female" else "2"
    await page.click(f"#QGender_{gender_option}")

    # Select date of birth
    await update.edit_text("Selecting date of birth.........")
    await page.select_option("#QDOB_day", label=data["QDOB_day"])
    await page.select_option("#QDOB_month", label=data["QDOB_month"])
    await page.select_option("#QDOB_year", label=data["QDOB_year"])

    # Select country of birth
    await update.edit_text("Selecting country of birth.........")
    await page.select_option("#QCountryOfBirth", label=data["QCountryOfBirth"])
    await asyncio.sleep(3)

    # Fill the State/Province/Region field
    await update.edit_text("Filling state/province/region.........")
    await page.fill("#QStateOfBirth", data["QStateOfBirth"])
    await asyncio.sleep(1)

    # Fill the Town/City
    await update.edit_text("Filling city of birth.........")
    await page.fill("#QCityOfBirth", data["QCityOfBirth"])

    # Fill the Passport Number field
    await update.edit_text("Filling passport number.........")
    await page.fill("#QPassportNbr", data["QPassportNbr"])

    # Select the country or territory of the passport by its text
    await page.evaluate('window.scrollBy(0, 300)')
    await asyncio.sleep(3)
    await update.edit_text("Selecting passport issue country.........")
    await page.select_option("#QPassportIssueCountry", label=data["QPassportIssueCountry"])
    await asyncio.sleep(3)

    # Choose the expiry date for the passport
    await update.edit_text("Selecting passport expiry date.........")
    await page.select_option("#QPassportExpiryDate_day", value=data["QPassportExpiryDate_day"])
    await asyncio.sleep(1)
    await page.select_option("#QPassportExpiryDate_month", value=data["QPassportExpiryDate_month"])
    await asyncio.sleep(1)
    await page.select_option("#QPassportExpiryDate_year", value=data["QPassportExpiryDate_year"])
    await asyncio.sleep(1)

    # Select "Single" option
    await update.edit_text("Selecting partnership status.........")
    await page.select_option("#QPartnershipStatus", label=data["QPartnershipStatus"])

    # Choose "No"
    await update.edit_text("Choosing applied visa before.........")
    await page.click("#QAppliedVisaBefore_2")  # Have you previously applied for a visa for New Zealand?

    # Residential Address
    # Fill in the country
    await update.edit_text("Filling residential address.........")
    await page.select_option("#QAppCountry", data["QAppCountry"])
    await asyncio.sleep(2)  # 1 second delay

    # Fill in the street address
    await page.fill("#QAppAddress1", data["QAppAddress1"])
    await asyncio.sleep(2)  # 1 second delay

    # Fill in the town/city
    await page.fill("#QAppCity", data["QAppCity"])
    await asyncio.sleep(1)  # 1 second delay

    # Fill in the state/province/region
    await page.select_option("#ResidentialCountryRegionStateLookupID",
                             data["ResidentialCountryRegionStateLookupID"])
    await asyncio.sleep(2)  # 1 second delay

    # Fill in the ZIP/post code
    await page.fill("#QAppPostCode", data["QAppPostCode"])
    await asyncio.sleep(2)  # 1 second delay

    # Fill contact form
    await fill_contact_form(page, data)

    # Select group and Agree
    await select_group_and_agree(page, data)

    pass


async def fourth_page(update, page, data):
    # Handle Pathway Student Visa question
    await update.edit_text("Answering Pathway Student Visa question...")
    pathway_visa_option = "1" if data.get("QPathwayVisa", "").lower() == "yes" else "2"
    await page.click(f"#QPathwayVisa_{pathway_visa_option}")
    await delay()  # Introduce delay

    # Handle Exchange Student question
    if pathway_visa_option == "2":
        await delay(1)  # Introduce delay wait for the exchange to apper then clcik

        await update.edit_text("Answering Exchange Student question...")
        exchange_student_option = "1" if data.get("QExchange", '').lower() == "yes" else "2"
        await page.click(f"#QExchange_{exchange_student_option}")
        await delay(3)  # Introduce delay

        if exchange_student_option == "1":
            await delay(3)  # Introduce delay
            await update.edit_text("Selecting Exchange Type...")
            await page.select_option("#QExchangeType", label=data.get("QExchangeType", "Tertiary exchange"))
            await delay()  # Introduce delay

    # Handle Scholarship question
    await update.edit_text("Answering Scholarship question...")
    scholarship_option = "1" if data.get("QScholarship", '').lower() == "yes" else "2"
    await page.click(f"#QScholarship_{scholarship_option}")
    await delay(2)  # Introduce delay

    if scholarship_option == "1":
        await update.edit_text("Selecting Scholarship Type...")

        # select the other schloaoship type
        await page.select_option("#QScholarshipType", label=data.get("QScholarshipType", ""))

        # Check if Scholarship Type is 'Other'

        if data.get("QScholarshipType", "").lower() == "other":
            await page.select_option("#QScholarshipType", label="Other")
            await delay(0.1)  # Introduce delay
            await page.fill("#QPleaseSpecify", data.get('QPleaseSpecify'))
            await delay(.2)  # Introduce delay

        else:
            # Check if Scholarship Type is 'Other Government' QScholarshipTypeGovernment
            # if data.get("QScholarshipType", "").lower() == "Other government supported":
            await page.select_option("#QScholarshipTypeGovernment",
                                     label=data.get("QScholarshipTypeGovernmentCountry", ""))
            await delay()  # Introduce delay

    # Fill the Intend to Enter New Zealand date
    await delay(1)  # Introduce delay
    await update.edit_text("Selecting Intend to Enter New Zealand date...")
    await page.select_option("#QIntendtoEnter_day", label=data.get("QIntendtoEnter_day", ''))
    await delay(1)  # Introduce delay
    await page.select_option("#QIntendtoEnter_month", label=data.get("QIntendtoEnter_month", ""))

    await delay(1)  # Introduce delay
    await page.select_option("#QIntendtoEnter_year", label=data.get("QIntendtoEnter_year", ''))

    ######     ######    ######    ######    ######    ######    ######    ######

    # Select the Total Stay Duration
    # await update.edit_text("Selecting Total Stay Duration...")
    # total_stay_duration = data.get("QTimeinNewZealand", '')
    # await page.click(f"#QTimeinNewZealand_{total_stay_duration[-1]}")
    async def select_stay_duration(page, data, update):
        stay_duration = data.get("QTimeinNewZealand", "")

        # Define the value corresponding to each option
        # options = {
        #     "6 months or less": "75f5654a-aeff-426e-8bbe-9f8990365b9e",
        #     "More than 6 months and up to 12 months": "6c2609b4-7167-4493-bdea-9fa26bd9581f",
        #     "More than 12 months and less than 24 months": "c1b15474-56b4-4ed1-b191-d27a341ab69d",
        #     "24 months or more": "5966e847-eef0-4f1c-89b1-d70e302754eb"
        # }

        options = {
            "6 months or less": "1",
            "More than 6 months and up to 12 months": "2",
            "More than 12 months and less than 24 months": "3",
            "24 months or more": "4"
        }

        # Select the appropriate radio button option based on the given data
        option_value = options.get(stay_duration, "")

        if option_value:
            await update.edit_text("Selecting stay duration...")
            await page.check(f"#QTimeinNewZealand_{option_value}")
            await delay()  # Introduce delay
            await update.edit_text("Stay duration selected.")
        else:
            await update.edit_text("Invalid stay duration provided.")

    await select_stay_duration(page, data, update)

    ######    ######     ######    ######    ######    ######    ######    ######    ######    ######

    ######    ######     ######    ######    ######    ######    ######    ######    ######    ######
    # # Handle Course Fee Exempt question
    # if data["QExchange"].lower() == "no" and data.get("QCurrentStudentVisa", "").lower() == "no":
    #     await update.edit_text("Answering Course Fee Exempt question...")
    #     course_fee_exempt_option = "1" if data["QCourseFeeExempt"].lower() == "yes" else "2"
    #     await page.click(f"#QCourseFeeExempt_{course_fee_exempt_option}")

    await update.edit_text("Answering Course Fee Exempt question...")
    # Wait for the element to exist with a timeout of 5 seconds
    try:
        await page.wait_for_selector("#QCourseFeeExempt_1", timeout=5000)
        # Click the appropriate option based on the data
        course_fee_exempt_option = "1" if data["QCourseFeeExempt"].lower() == "yes" else "2"
        await page.click(f"#QCourseFeeExempt_{course_fee_exempt_option}")
        await delay()  # Introduce delay
    except Exception as e:
        # Handle the case when the element doesn't exist within the timeout
        print("Element not found within 5 seconds:", e)

    ######    ######     ######    ######    ######    ######    ######    ######    ######    ######

    ######    ######     ######    ######    ######    ######    ######    ######    ######    ######

    # input("wait ")

    async def select_start_date(page, data, update):
        await update.edit_text("Selecting start date...")

        # Extract day, month, and year from the provided data
        day = data.get("QCourseStartDate_day", '30')
        month = data.get("QCourseStartDate_month", "April")
        year = data.get("QCourseStartDate_year", "2024")

        # Check if all necessary data is provided
        if day and month and year:
            # Select the day, month, and year from the dropdowns
            await page.select_option("#QCourseStartDate_day", label=day)
            await delay()  # Introduce delay
            await page.select_option("#QCourseStartDate_month", label=month)
            await delay()  # Introduce delay
            await page.select_option("#QCourseStartDate_year", label=year)
            await delay()  # Introduce delay

            await update.edit_text("Start date selected.")
        else:
            await update.edit_text("Incomplete start date provided.")

    await select_start_date(page, data, update)

    ######    ######     ######    ######    ######    ######    ######    ######    ######    ######

    ######    ######     ######    ######    ######    ######    ######    ######    ######    ######

    async def select_end_date(page, data, update):
        # Update the bot to indicate the current operation
        await update.edit_text("Selecting End Date...")

        # Extract end date components from the data dictionary
        end_date_day = data.get("QCourseFinishDate_day", "2")
        end_date_month = data.get("QCourseFinishDate_month", "April")
        end_date_year = data.get("QCourseFinishDate_year", "2025")

        # Fill in the end date fields
        await page.select_option("#QCourseFinishDate_day", label=end_date_day)
        await delay()  # Introduce delay
        await page.select_option("#QCourseFinishDate_month", label=end_date_month)
        await delay()  # Introduce delay
        await page.select_option("#QCourseFinishDate_year", label=end_date_year)
        await delay()  # Introduce delay

        # Update the bot to indicate the completion of the operation
        await update.edit_text("End Date Selected Successfully")

    await select_end_date(page, data, update)

    ######    ######     ######    ######    ######    ######    ######    ######    ######    ######

    ######    ######     ######    ######    ######    ######    ######    ######    ######    ######

    async def select_program_type(page, data, update):
        # Update the bot to indicate the current operation
        await update.edit_text("Selecting Program Type...")

        # Extract program type label from the data dictionary
        program_type_label = data.get("QProgramTypeLabel", "")

        # Define the mapping of program type labels to their corresponding values
        program_type_mapping = {
            "Primary": "ce591b5e-88d2-4b65-929a-51cbd7640ddb",
            "Secondary": "b9979391-8d93-4724-979d-f451d900908a",
            "Undergraduate": "966692a6-3dfb-49c6-9124-3b1355852796",
            "Postgraduate excluding PhD": "715ffdf6-381a-4c27-8b29-4067b7d80052",
            "PhD": "ea697029-ab8d-4b43-99ee-cc30883bd102",
            "English Language": "1d32e94b-744d-4afc-b839-6d16e3a2d7e2"
        }

        # Get the corresponding value for the given label
        program_type_value = program_type_mapping.get(program_type_label, "")

        # Select the program type from the dropdown if a valid value is found
        if program_type_value:
            await page.select_option("#QProgramType", value=program_type_value)
            await delay()  # Introduce delay
            await update.edit_text("Program Type Selected Successfully")

            # Check if the program type is "Primary" or "Secondary" to handle additional fields
            if program_type_label.lower() in ["primary", "secondary"]:
                await handle_school_year(page, data, update)

            elif program_type_label.lower() == "undergraduate":
                await handle_undergraduate_fields(page, data, update)

            elif program_type_label == "Postgraduate excluding PhD":
                await handle_postgraduate_fields(page, data, update)


        else:
            await update.edit_text("Invalid Program Type Label Provided")

    async def handle_school_year(page, data, update):
        # Update the bot to indicate the current operation
        await update.edit_text("Selecting School Year...")

        # Define the mapping of school year labels to their corresponding values for primary
        primary_school_year_mapping = {
            "Year 01": "97a7414a-3e8b-4a16-9550-d3c08eb24367",
            "Year 02": "58f08a19-e7b5-4bbf-9171-2346311bf154",
            "Year 03": "24ff2b0b-312f-4720-a58a-9147192731c1",
            "Year 04": "dcc168f4-af3c-408f-ae8c-0d9621b41d47",
            "Year 05": "1cb3b655-0890-437c-a6f0-858a84cf5af5",
            "Year 06": "b9a4bb1d-2708-48b3-bee6-aecf00b16bec",
            "Year 07": "ede4161a-8dc5-4fc3-9149-42742fa96df0",
            "Year 08": "c62d37a5-7aa6-463f-9268-5b680093c688"
        }

        # Define the mapping of school year labels to their corresponding values for secondary
        secondary_school_year_mapping = {
            "Year 09": "e386d1c4-2d93-430d-ba02-00dea244ec45",
            "Year 10": "13f78db7-abb5-49a6-932d-fd7547c99be0",
            "Year 11": "a5ef7017-6279-4b7e-86a5-432d3fb6f8f2",
            "Year 12": "de7341f9-61b9-49b8-91f5-c3540c2bb90d",
            "Year 13": "288ff5ac-af86-48a4-be7b-a2e99119327d"
        }

        # Extract school year label from the data dictionary
        school_year_label = data.get("QSchoolYear", "")

        # Get the corresponding value for the given label based on primary or secondary
        if school_year_label in primary_school_year_mapping:
            school_year_value = primary_school_year_mapping.get(school_year_label, "")
            dropdown_id = "#QSchoolYearPrimary"
            await page.select_option("#QProgramType", value="Primary")
        elif school_year_label in secondary_school_year_mapping:
            school_year_value = secondary_school_year_mapping.get(school_year_label, "")
            dropdown_id = "#QSchoolYearSecondary"
            await page.select_option("#QProgramType", value="Secondary")
        else:
            school_year_value = ""
            dropdown_id = ""

        # Select the school year from the dropdown if a valid value is found
        if school_year_value and dropdown_id:
            await page.select_option(dropdown_id, value=school_year_value)
            await update.edit_text("School Year Selected Successfully")
        else:
            await update.edit_text("Invalid School Year Label Provided")

    async def handle_undergraduate_fields(page, data, update):
        await update.edit_text("Handling Undergraduate fields...")

        # Fill in the qualification/program you will be studying
        qualification = data.get("Qqualification", "English")
        if qualification:
            await page.fill("#Qqualification", qualification)
            await update.edit_text("Qualification/Program Entered Successfully")
        else:
            await update.edit_text("No Qualification/Program Provided")

        # Select the 120 credits option
        await select_120_credits(page, data, update)

    async def select_120_credits(page, data, update):
        await update.edit_text("Selecting 120 credits option...")

        # Check if the program is 120 credits or more
        credits_120_or_more = data.get("Q120credits", "")
        if credits_120_or_more.lower() == "yes":
            await page.check("#Q120credits_1")  # Select "Yes"
            await update.edit_text("Program is 120 credits or more")
        elif credits_120_or_more.lower() == "no":
            await page.check("#Q120credits_2")  # Select "No"
            await update.edit_text("Program is less than 120 credits")
        else:
            await update.edit_text("Invalid value provided for 120 credits option")

    # If the logic is Postgraduate ut excluding PDH that is master degree

    async def handle_postgraduate_fields(page, data, update):
        await update.edit_text("Handling Postgraduate fields...")

        # Select the qualification/program you will be studying
        await select_postgraduate_program(page, data, update)

        # select the 120 credit and the subject
        await handle_undergraduate_fields(page, data, update)

    async def select_postgraduate_program(page, data, update):
        await update.edit_text("Selecting Postgraduate program...")

        # Dictionary mapping program names to their corresponding values
        program_mapping = {
            "Accountancy": "bf84eb94-98bd-457a-9561-084b2c805f6e",
            "Aerospace Engineering and Technology": "881dcbcc-d564-4cce-a838-ab3f4eccc6bc",
            "Agricultural Science": "9ee13dd3-bb63-4a25-a000-58b2ccd08497",
            "Agriculture": "58db7d66-6170-41fb-8ac4-d9fd5c95cb83",
            "Archaeology": "8d7a566b-4096-45a2-a2b4-7adafc9e28dc",
            "Architecture": "7819b989-4396-465d-9588-16e9bd81e939",
            "Art History": "fc7f079b-51b6-4720-9635-9b99888a00fc",
            "Astronomy": "0440de22-6fc2-4605-a4fb-c27506f958a7",
            "Audiology": "bbfcad71-c1de-43be-b6b7-0425389f7e77",
            "Automotive Engineering and Technology": "b7e63b9d-caec-48a5-836d-2545818caf9e",
            "Biological Sciences": "7c67445a-52eb-4e77-8811-3171cbca76e0",
            "Business": "df87d4f4-7931-49df-ac74-2b77521cb7b7",
            "Chemical Engineering": "2996bc7c-b0d5-4679-bbd8-aea265d2d346",
            "Chemical Sciences": "e0195c98-6a74-47dd-a4d2-27d81309fd78",
            "Civil Engineering": "cdd221a7-26d4-4620-b7ea-4b22bf1200d4",
            "Classical Studies": "7e5c7fef-cd7a-4ad2-a29f-5acbc110a835",
            "Communication and Media Studies": "60b26ce1-c490-4868-81fd-620f0e045174",
            "Computer Science": "8854ed5e-34b7-42bb-aa17-c33385bacec2",
            "Dental Studies": "e74d654d-0b88-4e1d-9b99-8b7d5f7eee7f",
            "Earth Sciences": "78b85434-0603-4247-a633-cee355bc1c2c",
            "Economics": "a4f07898-7b41-43b1-a930-8b4d839dbd09",
            "Education Studies": "a8eeb0a4-6191-441a-9c86-2d744993c5c8",
            "Electrical and Electronic Engineering and Technology": "ba1a3b4d-da58-41dc-8b02-32745ba1c6b9",
            "English": "425f101a-e1de-4ec0-9cb7-b8c78bf95e5b",
            "Environmental Studies": "c8095c11-b9d9-4572-bc97-033e784b5253",
            "Epidemiology": "ec0b2ce8-443b-477b-8b11-7326f2885359",
            "Finance": "e936d33b-1112-4776-849e-843260d78e87",
            "Fisheries Studies": "3c8df524-eeb9-406c-a4ad-0ad75e10c116",
            "Foreign Languages": "caa35706-0641-4d53-a78f-007f91371c31",
            "Forestry Studies": "c31c4ccb-adf9-4b15-ba6e-0b7981faa85b",
            "Geomatic Engineering": "01028b83-0e97-4ec6-8170-7c05cef46cdf",
            "Graphic and Design Studies": "158c752c-b5af-4eb8-8f27-bd665fa4fe39",
            "History": "4c4e365b-7fb7-4d5e-9491-0d629b34dc6e",
            "Horticulture and Viticulture": "9fc09813-e2cd-407b-922b-0ce7477ce9ae",
            "Information Systems": "ca06d284-de84-440e-85fa-486a4c2f468d",
            "Information Technology not elsewhere classified": "a6424d9f-a750-4970-8e5d-f2f03d968327",
            "Law": "a45c987d-68a2-4509-82b6-4f4a4fa39820",
            "Librarianship, Information Management and Curatorial Studies": "e4ad0cf9-f871-4732-bac0-a7130a3428fb",
            "Linguistics": "9cd17236-8e98-4061-96ca-141bd1c0a1d8",
            "Management": "b25b0d45-db4e-48d7-879f-33d6079e0c09",
            "Maritime Engineering and Technology": "f8230f8b-d2de-445a-9ce1-b900bfc1db4f",
            "Mathematical Sciences": "5c47dbaf-d716-476c-b480-58bfdc73a761",
            "Mechanical and Industrial Engineering and Technology": "2349136d-15a1-482d-8df2-b4a15aad4b9a",
            "Medical Studies": "a5b5f93d-5640-40c9-aa06-9281dca0b0f6",
            "Nursing": "a94e417e-14c7-47f3-abd8-978749ccb7b7",
            "Optical Science": "800a1c45-795a-4fef-b5d3-cc91c32c1127",
            "Other Creative Arts": "42680058-48a7-421d-b1f8-547ae9583bdf",
            "Other Education": "ab82b82d-a72c-4c79-ba68-a55b99c3efa9",
            "Other Engineering": "b4cb9f3d-c5dd-4d72-9e07-9b58a8cf04e8",
            "Other Health": "01b481b7-c441-46f0-8ca7-cf7d7e276a68",
            "Other Humanities": "c911de4e-3f52-4efb-987d-3159ef07bd41",
            "Other Management and Commerce": "8c680395-3274-46bd-9b6a-436951ff293d",
            "Other Natural and Physical Sciences": "f6379e07-ec85-4b78-b06b-4c25d3324f51",
            "Pathology": "da6983db-ef39-4fd6-8574-fcf7b593f974",
            "Performing Arts": "9171ab7a-b63a-4b30-963b-9724b099142a",
            "Pharmacy": "c839aff4-2073-4621-b4a5-905a44d3be8c",
            "Philosophy": "9c5c8234-bb0c-45d3-8ac3-40c356e68078",
            "Physics": "b7a981e2-091a-4691-934b-c164f0a921f4",
            "Policy Studies": "2946c80f-2696-4d1c-9929-4a64a42421de",
            "Political Science": "3de24a67-e32c-4459-9c04-1a666d22a7c9",
            "Process and Resources Engineering": "dc7eb894-b189-4c06-b5c5-97ad6ffb17c1",
            "Psychology": "411ae2b1-e315-4922-ae34-5f413eac94aa",
            "Public Health": "1d17b861-4e2a-4d33-b0ea-ad975b9de53d",
            "Radiography": "1470bd65-a7ee-437a-9b85-53c0645d47f2",
            "Radiology": "df6649a3-cfbf-4934-814e-02ce43116f38",
            "Rehabilitation Therapies": "cd35c154-1282-4a6d-abf2-e1c20bcae3d1",
            "Sales and Marketing": "614c19c7-10e2-4796-9b24-358f962e604b",
            "Social Work": "5e64b319-d2b2-4ad0-a1be-04ee7b7a5055",
            "Sociology": "17de87fa-46d0-4eef-91c0-6ef965db4d76",
            "Speech Science": "9b4aa33f-2d89-490e-b0d3-a0e5970bbcb5",
            "Sport and Recreation": "0e0f642f-986b-407b-b783-30a6dec25520",
            "Teacher Education": "bfa14550-cb1c-4376-a026-fa6150698fb0",
            "Tourism": "ea088b00-6d2f-4bb3-bc65-622e499e365c",
            "Veterinary Studies": "1510e249-f42d-4d54-b3a8-b3db9bb88c8e",
            "Visual Arts and Crafts": "aa491086-d026-4764-9ef9-bdb0419b379e",
            "Women's Studies": "7da22159-8f0f-4fc8-8d28-3b50ff0b3f02",
        }

        # Get the name of the postgraduate program from the data
        program_name = data.get("Postgraduate_program_name", "Accountancy")
        print(program_name)  # Debugging purpose

        if program_name:
            # Check if the program name exists in the mapping
            if program_name.title() in program_mapping:
                # Get the value from the mapping
                program_value = program_mapping[program_name]
                # Select the program using its value
                await page.select_option("#rptQPostgraduate-0-QPostgraduate", value=program_value)
                await update.edit_text(f"Postgraduate program '{program_name}' selected successfully")
            else:
                await update.edit_text(f"No mapping found for '{program_name}'")
        else:
            await update.edit_text("No Postgraduate program name provided")

    await select_program_type(page, data, update)

    ######    ######     ######    ######    ######    ######    ######    ######    ######    ######

    ######    ######     ######    ######    ######    ######    ######    ######    ######    ######

    async def enter_education_provider(page, data, update):
        # Update the bot to indicate the current operation
        await update.edit_text("Entering Education Provider...")

        # Extract education provider name from the data dictionary
        education_provider_name = data.get("QEducationProviderName", "")

        # Fill in the education provider name in the input field
        if education_provider_name:
            await page.fill("#QEducationProvider", education_provider_name)
            await delay()  # Introduce delay
            await update.edit_text("Education Provider Entered Successfully")
        else:
            await update.edit_text("No Education Provider Name Provided")

    await enter_education_provider(page, data, update)
    delay_time = 3
    await update.edit_text(f"Delaying for {delay_time} before proceeding ")

    await delay(delay_time)


######    ######     ######    ######    ######    ######    ######    ######    ######    ######

######    ######     ######    ######    ######    ######    ######    ######    ######    ######


async def fifth_page(update, page, data):
    # input("wait")
    # Handle Financial Support Options
    await update.edit_text("Answering Financial Support Options question...")
    financial_support_options = []

    if data.get("QHasThirdPartyFinancialUndertaking", "true").lower() == "true":
        financial_support_options.append("HasThirdPartyFinancialUndertaking")
        await page.check("#FinancialSupportOptions_1")


    if data.get("QHasSufficientFunds", "true").lower() == "true":
        financial_support_options.append("HasSufficientFunds")
        await page.check("#FinancialSupportOptions_2")

    if data.get("QAreLivingCostsPaid", "true").lower() == "true":
        financial_support_options.append("AreLivingCostsPaid")
        await page.check("#FinancialSupportOptions_3")

    if data.get("QHasFullScholarshipAward", "true").lower() == "true":
        financial_support_options.append("HasFullScholarshipAward")
        await page.check("#FinancialSupportOptions_4")

    if data.get("QHasSponsorship", "true").lower() == "true":
        financial_support_options.append("HasSponsorship")
        await page.check("#FinancialSupportOptions_5")

    # Handle Arrangements Travel
    await update.edit_text("Answering Arrangements Travel question...")
    arrangements_travel = []

    if data.get("QPrepurchasedTravel", "true").lower() == "true":
        arrangements_travel.append("Prepurchased")
        await page.check("#ArrangementsTravel_1")

    if data.get("QHasSufficientFundsForTravel", "true").lower() == "true":
        arrangements_travel.append("HasSufficientFunds")
        await page.check("#ArrangementsTravel_2")

    if data.get("QThirdPartyFinancialUndertakingForTravel", "true").lower() == "true":
        arrangements_travel.append("HasThirdPartyFinancialUndertaking")
        await page.check("#ArrangementsTravel_3")

    await delay(3)


######    ######     ######    ######    ######    ######    ######    ######    ######    ######

######    ######     ######    ######    ######    ######    ######    ######    ######    ######




async def sixth_page(update, page, data):
    # Handle Tuberculosis (TB) question
    await update.edit_text("Answering Tuberculosis (TB) question...")
    tb_option, tb_details = await handle_question(page, "QTB", data.get("QTB", "No"), data.get("QTBDetails", ""))

    # Handle Renal Dialysis question
    await update.edit_text("Answering Renal Dialysis question...")
    renal_dialysis_option, renal_dialysis_details = await handle_question(page, "QRenalDialysis",
                                                                          data.get("QRenalDialysis", "No"),
                                                                          data.get("QRenalDialysisDetails", ""))

    # Handle Hospital Care question
    await update.edit_text("Answering Hospital Care question...")
    hospital_care_option, hospital_care_details = await handle_question(page, "QHospitalCare",
                                                                        data.get("QHospitalCare", "No"),
                                                                        data.get("QHospitalCareDetails", ""))

    # Handle Residential Care question
    await update.edit_text("Answering Residential Care question...")
    residential_care_option, residential_care_details = await handle_question(page, "QResidentialCare",
                                                                              data.get("QResidentialCare", "No"),
                                                                              data.get("QResidentialCareDetails", ""))

    # Handle Special Education Services question
    await update.edit_text("Answering Special Education Services question...")
    special_education_option, special_education_details = await handle_question(page, "QSpecialEducationServices",
                                                                                data.get("QSpecialEducationServices",
                                                                                         "No"), data.get(
            "QEducationServiceDetails", ""))

    # Handle Health Insurance Declaration
    await update.edit_text("Answering Health Insurance Declaration...")
    await page.check("#QHeathIncDec")

    # Continue to the next page
    await delay(3)
    # await update.edit_text("Moving to the next page...")
    # await page.click('input[name="_continueButton"]')


async def handle_question(page, question_id, option_value, details_value):
    option_id = await handle_radio_option(page, question_id, option_value)
    details = await handle_text_input(page, f"{question_id}Details", details_value, option_id == f"{question_id}_1")
    return option_id, details


async def handle_radio_option(page, question_id, option_value):
    # Convert "No" to False and "Yes" to True
    # print("handle_radio_option",option_value, question_id)
    option_bool = option_value.lower() == 'no'

    # Determine the option ID based on the boolean value
    option_id = f"{question_id}_{int(option_bool) + 1}"

    # Click on the corresponding option
    await page.click(f"#{option_id}")

    return option_id


async def handle_text_input(page, input_id, input_value, should_fill):
    if input_id == "QSpecialEducationServicesDetails":  # The QSpecialEducationServicesDetails is not same to the handle input text
        input_id = "QEducationServiceDetails"

    if should_fill:
        # print(f"#{input_id}")
        await page.fill(f"#{input_id}", input_value)
    return input_value


######    ######     ######    ######    ######    ######    ######    ######    ######    ######

######    ######     ######    ######    ######    ######    ######    ######    ######    ######


async def seventh_page(update, page, data):
    # Handle Convicted question
    convicted_option, convicted_details = await handle_question_7(page, "Qconvicted", data.get("Qconvicted", "No"),
                                                                  data.get("QconvictedDetails", ""))

    # Handle Investigation question
    investigation_option, investigation_details = await handle_question_7(page, "QInvestigation",
                                                                          data.get("QInvestigation", "No"),
                                                                          data.get("QInvestigationDetails", ""))

    # Handle Charges question
    charges_option, charges_details = await handle_question_7(page, "Qcharges", data.get("Qcharges", "No"),
                                                              data.get("QchargesDetails", ""))

    # Handle Excluded question
    excluded_option, excluded_details = await handle_question_7(page, "QExcluded", data.get("QExcluded", "No"),
                                                                data.get("QExcludedDetails", ""))

    # Handle Refused question
    refused_option, refused_details = await handle_question_7(page, "QRefused", data.get("QRefused", "No"),
                                                              data.get("QRefusedDetails", ""))

    # Handle Removed question
    removed_option, removed_details = await handle_question_7(page, "QRemoved", data.get("QRemoved", "No"),
                                                              data.get("QRemovedDetails", ""))

    # Handle Questioning question
    questioning_option, questioning_details = await handle_question_7(page, "QQuestioning",
                                                                      data.get("QQuestioning", "No"),
                                                                      data.get("QQuestioningDetails", ""))

    # Handle Currently Investigated question
    currently_investigated_option, currently_investigated_details = await handle_question_7(page,
                                                                                            "QCurrentlyInvestigated",
                                                                                            data.get(
                                                                                                "QCurrentlyInvestigated",
                                                                                                "No"), data.get(
            "QCurrentlyInvestigatedDetails", ""))

    # Handle Current Charges question
    current_charges_option, current_charges_details = await handle_question_7(page, "QCurrentCharges",
                                                                              data.get("QCurrentCharges", "No"),
                                                                              data.get("QCurrentChargesDetails", ""))

    # Continue to the next page

    # input("wait for 7 confirmation")
    # await update.edit_text("Moving to the next page...")
    # await page.click('input[name="_continueButton"]')


async def handle_question_7(page, question_id, option_value, details_value):
    option_id = await handle_radio_option_7(page, question_id, option_value)
    details = await handle_text_input_7(page, f"{question_id}Details", details_value, option_id == f"{question_id}_1")
    return option_id, details


async def handle_radio_option_7(page, question_id, option_value):
    if option_value.lower() == "yes":
        option_id = f"{question_id}_1"  # Select the second option for "Yes"
    else:
        option_id = f"{question_id}_2"  # Select the first option for "No" (default)
    await page.click(f"#{option_id}")
    return option_id


async def handle_text_input_7(page, input_id, input_value, should_fill):
    if should_fill:
        await page.fill(f"#{input_id}", input_value)
    return input_value


######    ######     ######    ######    ######    ######    ######    ######    ######    ######

######    ######     ######    ######    ######    ######    ######    ######    ######    ######


async def eighth_page(update, page, data):
    # Handle New Zealand Business Number (NZBN)
    await update.edit_text("Entering New Zealand Business Number (NZBN)...")
    nzbn = data.get("QEmployeeHistoryRe-0-QNZBusinessNumber", "")
    await page.type("#QEmployeeHistoryRe-0-QNZBusinessNumber", nzbn)

    await delay()

    # Handle Name of Company/Organization
    await update.edit_text("Entering Name of Company/Organization...")
    company_name = data.get("QEmployeeHistoryRe-0-QEHEmployer2", "")
    await page.type("#QEmployeeHistoryRe-0-QEHEmployer2", company_name)

    await delay(1)

    # Handle Type of Work/Occupation/Job Title
    await update.edit_text("Entering Type of Work/Occupation/Job Title...")
    job_title = data.get("QEmployeeHistoryRe-0-QTypeWork", "")
    await page.type("#QEmployeeHistoryRe-0-QTypeWork", job_title)

    await delay(1)

    # Handle Start Date
    await update.edit_text("Entering Start Date...")
    start_date = data.get("QEmployeeHistoryRe-0-QEHPartialStartDate", "")
    await page.type("#QEmployeeHistoryRe-0-QEHPartialStartDate", start_date)

    await delay()

    # Handle End Date
    await update.edit_text("Entering End Date...")
    end_date = data.get("QEmployeeHistoryRe-0-QEHPartialEndDate", "")
    await page.type("#QEmployeeHistoryRe-0-QEHPartialEndDate", end_date)

    await delay()

    ##### TRY THE JOB TITLE AGAIN #######
    # Handle Type of Work/Occupation/Job Title
    await update.edit_text("Entering Type of Work/Occupation/Job Title...")
    job_title = data.get("QEmployeeHistoryRe-0-QTypeWork", "")
    await page.type("#QEmployeeHistoryRe-0-QTypeWork", job_title)

    await delay(1)

    # Handle Country/Territory
    # await update.edit_text("Entering Country/Territory...")
    # country_territory = data.get("QEmployeeHistoryRe-0-QEHLocationCountry2", "")
    # await page.fill("#QEmployeeHistoryRe-0-QEHLocationCountry2", country_territory)

    # Handle Territory
    await update.edit_text("Selecting Territory...")
    territory = data.get("QEmployeeHistoryRe-0-QEHLocationCountry2", "")
    await page.select_option("#QEmployeeHistoryRe-0-QEHLocationCountry2", value=territory)

    await delay()

    # Handle State/Province/Region
    await update.edit_text("Entering State/Province/Region...")
    state_province_region = data.get("QEmployeeHistoryRe-0-QEHLocationState2", "")
    await page.fill("#QEmployeeHistoryRe-0-QEHLocationState2", state_province_region)

    await delay()

    # Handle Town/City
    await update.edit_text("Entering Town/City...")
    town_city = data.get("QEmployeeHistoryRe-0-QEHLocationTown", "")
    await page.fill("#QEmployeeHistoryRe-0-QEHLocationTown", town_city)

    await delay()

    # Handle Current Employer Checkbox
    await update.edit_text("Selecting Current Employer option...")
    current_employer = data.get("QEmployeeHistoryRe-0-QEHCurrentEmployer2", "")
    if current_employer.lower() == "yes":
        await page.check("#QEmployeeHistoryRe-0-QEHCurrentEmployer2")

    # Continue to the next page
    # await update.edit_text("Moving to the next page...")
    # await page.click('input[name="_continueButton"]')


######    ######     ######    ######    ######    ######    ######    ######    ######    ######

######    ######     ######    ######    ######    ######    ######    ######    ######    ######

async def ninth_page(update, page, data):
    # Provide additional information to assist with the assessment of your visa application
    await update.edit_text("Filling out additional information...")

    # Handle the question "Do you have any contacts in New Zealand?"
    await update.edit_text("Do you have any contacts in New Zealand?")
    contacts_in_nz = data.get("QNZContacts", "")
    if contacts_in_nz.lower() == "yes":
        await page.check("#QNZContacts_1")

        await delay()

        await update.edit_text("Filling out contact details...")
        # Fill out contact details if the user has contacts in New Zealand
        family_name = data.get("FamilyName", "")
        given_names = data.get("GivenNames", "")

        # Select the date of birth
        dob_day = data.get("DOBDay", "")
        dob_month = data.get("DOBMonth", "")
        dob_year = data.get("DOBYear", "")
        if dob_day and dob_month and dob_year:
            # Select day
            await page.select_option("#rptNZContacts-0-QCDOB_day", value=dob_day)
            # Select month
            await page.select_option("#rptNZContacts-0-QCDOB_month", value=dob_month)
            # Select year
            await page.select_option("#rptNZContacts-0-QCDOB_year", value=dob_year)

        # Select the relationship to the contact in New Zealand
        relationship_value = data.get("RelationshipValue", "")
        if relationship_value:  # rptNZContacts-0-QCRelationship
            await page.select_option("#rptNZContacts-0-QCRelationship", value=relationship_value)

        address = data.get("Address", "")
        telephone_cc = data.get("TelephoneCC", "")
        telephone_ac = data.get("TelephoneAC", "")
        telephone_num = data.get("TelephoneNum", "")

        ## Mobile

        mobile_telephone_cc = data.get("MobileTelephoneCC", "")

        mobile_telephone_num = data.get("MobileTelephoneNum", "")

        email = data.get("Email", "")

        # Fill out the contact details using page.fill()
        await page.fill("#rptNZContacts-0-QCFamilyName", family_name)
        await page.fill("#rptNZContacts-0-GivenFirstNames", given_names)

        await page.fill("#rptNZContacts-0-QCAddress1", address)
        await page.fill("#rptNZContacts-0-QCTelephone_cc", telephone_cc)
        await page.fill('#rptNZContacts-0-QCTelephone_ac', telephone_ac)
        await page.fill("#rptNZContacts-0-QCTelephone_num", telephone_num)

        # Mobile fill up
        await page.fill("#rptNZContacts-0-QCMobile_cc", mobile_telephone_cc)
        await page.fill('#rptNZContacts-0-QCMobile_num', mobile_telephone_num)
        await  delay()
        await page.fill("#rptNZContacts-0-QCMobile_cc", mobile_telephone_cc)  # again

        await page.fill("#rptNZContacts-0-QCEmail", email)


    elif contacts_in_nz.lower() == "no":
        await page.check("#QNZContacts_2")


async def tenth_page(update, page, data):
    # Retrieve values from the CSV file using data.get
    apply_on_behalf = data.get("QApplyOnBehalf", "yes")  # Default value is "No" if not found
    apply_on_behalf_type_key = data.get("QApplyOnBehalfType", "Licensed immigration adviser")
    apply_on_behalf_type_map = {
        "Licensed immigration adviser": "QApplyOnBehalfType_1",
        "Exempt from licensing": "QApplyOnBehalfType_2",
        "Parent or guardian": "QApplyOnBehalfType_3",
        "Assisting the applicant": "QApplyOnBehalfType_4"
    }
    apply_on_behalf_type_key = data.get("QApplyOnBehalfType", "Licensed immigration adviser")
    on_behalf_id = apply_on_behalf_type_map.get(apply_on_behalf_type_key, "QApplyOnBehalfType_1")

    limited_details = data.get("QLimitedDetails", "")
    licence_number = data.get("QLicenceNumber", "")
    assisting_person_last_name = data.get("QAssistingPersonLastName", "")
    assisting_person_first_name = data.get("QAssistingPersonFirsttName", "")
    nz_business_number = data.get("QNZBusinessNumber", "")
    assisting_person_company_name = data.get("QAssistingPersonCompanyName", "")
    assisting_person_address = data.get("QAssistingPersonAddress", "")
    assisting_person_telephone = data.get("QAssistingPersonTelephone", "")
    assisting_person_mobile = data.get("QAssistingPersonMobile", "")
    assisting_person_email = data.get("QAssistingPersonEmail", "")

    # Choose "Yes" or "No" for the first question
    if apply_on_behalf.lower() == "yes":
        await page.click('input#QApplyOnBehalf_1')  # Click "Yes" option

        # Choose the selected option for the second question
        # on_behalf_id = apply_on_behalf_type_map.get(apply_on_behalf_type_key)

        await page.click(f'#{on_behalf_id}')

        # Check if the selected option should be "Full" for the third question

        # Retrieve values from the CSV file using data.get
        licence_details_key = data.get("QLicenceDetails", "")  # Default value is empty if not found

        # Map the licence details key to the corresponding option value
        licence_details_map = {
            "Full": "1a657404-e726-4846-bb5b-84e7796e8e51",
            "Provisional": "5dfe9c29-2852-468b-bb8d-b46d5ebeb0a1",
            "Limited": "958552fa-03a8-44a3-9158-8487761651ee"
        }

        # Click the select element and choose the option corresponding to the licence details key
        await page.select_option('#QLicenceDetails', value=licence_details_map.get(licence_details_key,
                                                                                   "1a657404-e726-4846-bb5b-84e7796e8e51"))

        # Fill in the details for the additional fields
        await page.fill('#QLimitedDetails', limited_details)
        await page.fill('#QLicenceNumber', licence_number)
        await page.fill('#QAssistingPersonLastName', assisting_person_last_name)
        await page.fill('#QAssistingPersonFirsttName', assisting_person_first_name)
        await page.fill('#QNZBusinessNumber', nz_business_number)
        await page.fill('#QAssistingPersonCompanyName', assisting_person_company_name)
        await page.fill('#QAssistingPersonAddress', assisting_person_address)

        await page.fill('#QAssistingPersonTelephone_cc', assisting_person_telephone)
        #
        await page.fill('#QAssistingPersonTelephone_ac', assisting_person_telephone)
        await page.fill('#QAssistingPersonTelephone_num', assisting_person_telephone)

        # QAssistingPersonTelephone_num

        # QAssistingPersonMobile_cc
        # QAssistingPersonMobile_num
        await page.fill('#QAssistingPersonMobile_cc', assisting_person_mobile)
        await page.fill('#QAssistingPersonMobile_num', assisting_person_mobile)

        await page.fill('#QAssistingPersonEmail', assisting_person_email)

    else:
        await page.click('input#QApplyOnBehalf_2')  # Click "No" option


######    ######     ######    ######    ######    ######    ######    ######    ######    ######

######    ######     ######    ######    ######    ######    ######    ######    ######    ######

async def main(update=None, bot=None):
    try:
        async with async_playwright() as p:
            # browser = await p.chromium.launch(headless=False)
            # context = await browser.new_context()
            # page = await context.new_page()
            browser = await p.chromium.launch(
                headless=False,
                # downloads_path='downloads',  # Set the directory for downloads
                slow_mo=1000,  # Slow down Playwright operations by 1 second (for debugging)
                # chromium_sandbox=False,  # Disable Chromium sandbox (for testing purposes)
            )
            context = await browser.new_context()
            page = await context.new_page()



            url = "https://eforms.online.immigration.govt.nz/igms/eforms/online-services/new/Student%20Visa%20Application"

            # url='https://eforms.online.immigration.govt.nz/igms/eforms/online-services/SVA240434094/step/4'
            await page.goto(url)

            # Read data from CSV file
            with open("data.csv", "r") as csv_file:
                reader = csv.reader(csv_file)
                # data = next(reader)  # Assuming a single row in the CSV file
                data = transform_data(list(reader))


            # Login credentials
            await first_page(update, page, data)

            recent_message = await is_next_page(update, bot=bot, page=page,
                                                mode='login')  # should i proceed to next page or not?

            if recent_message:
                update = recent_message
            # await update.edit_text("Clicking Next button.........")
            # await page.click("button#next")
            # await asyncio.sleep(0.1)
            # await page.wait_for_load_state("domcontentloaded")

            # # Wait for the page to load
            # await page.wait_for_selector("#SCStudentVisa_1")
            # await asyncio.sleep(.1)

            await second_page(update, page, data)


            recent_message = await is_next_page(update, bot=bot, page=page)  # should i proceed to next page or not?

            if recent_message:
                update = recent_message


            await handle_next_button(page, update, bot)  # this is Page 2

            # await page.click("button.next")
            #   await page.wait_for_load_state(state='domcontentloaded')

            await third_page(update, page, data)


            await update.edit_text("Downloading pdf.....")
            await download_pdf_preview(page, bot, index='3')

            recent_message = await is_next_page(update, bot=bot, page=page)  # should i proceed to next page or not?
            if recent_message:
                update = recent_message

            await handle_next_button(page, update, bot)  # this is Page 3

            await fourth_page(update, page, data)

            await update.edit_text("Downloading pdf.....")
            await download_pdf_preview(page, bot, index='4')

            recent_message = await is_next_page(update, bot=bot, page=page)  # should i proceed to next page or not?
            if recent_message:
                update = recent_message

            await handle_next_button(page, update, bot)  # this is Page 4

            # input("wait first bro ")

            await fifth_page(update, page, data)

            await update.edit_text("Downloading pdf.....")
            await download_pdf_preview(page, bot, index='5')
            # Check if we have a pop up
            # await check_pop_up(page, update, bot, index='5')

            recent_message = await is_next_page(update, bot=bot, page=page)  # should i proceed to next page or not?
            if recent_message:
                update = recent_message

            await handle_next_button(page, update, bot)  # this is Page 5

            await sixth_page(update, page, data)

            await update.edit_text("Downloading pdf.....")
            await download_pdf_preview(page, bot, index='6')

            # Check if we have a pop up
            # await check_pop_up(page, update, bot, index='6')

            recent_message = await is_next_page(update, bot=bot, page=page)  # should i proceed to next page or not?
            if recent_message:
                update = recent_message

            await handle_next_button(page, update, bot)  # this is Page 6

            await seventh_page(update, page, data)

            await update.edit_text("Downloading pdf.....")
            await download_pdf_preview(page, bot, index='7')

            # Check if we have a pop up

            # await check_pop_up(page,update,bot,index='7')

            recent_message = await is_next_page(update, bot=bot, page=page)  # should i proceed to next page or not?
            if recent_message:
                update = recent_message

            await handle_next_button(page, update, bot)  # this is Page 7

            ### Start eight page

            await eighth_page(update, page, data)

            await update.edit_text("Downloading pdf.....")
            await download_pdf_preview(page, bot, index='8')

            # Check if we have a pop up

            # await check_pop_up(page,update,bot,index='7')

            recent_message = await is_next_page(update, bot=bot, page=page)  # should i proceed to next page or not?
            if recent_message:
                update = recent_message

            await handle_next_button(page, update, bot)  # this is Page 8

            await ninth_page(update, page, data)

            await update.edit_text("Downloading pdf.....")
            await download_pdf_preview(page, bot, index='9')

            # Check if we have a pop up

            # await check_pop_up(page,update,bot,index='7')

            recent_message = await is_next_page(update, bot=bot, page=page)  # should i proceed to next page or not?
            if recent_message:
                update = recent_message

            await handle_next_button(page, update, bot)  # this is Page 8

            await tenth_page(update, page, data)



            await update.edit_text("Downloading pdf.....")
            await download_pdf_preview(page, bot, index='10')

            # Check if we have a pop up

            # await check_pop_up(page,update,bot,index='7')

            recent_message = await is_next_page(update, bot=bot, page=page)  # should i proceed to next page or not?
            if recent_message:
                update = recent_message

            await handle_next_button(page, update, bot)  # this is Page 10

            # # check error message
            # await page.click("button.next")
            # await page.wait_for_load_state("domcontentloaded")

            ## END OF FIRsT PAGE ######

            await bot.message.reply_text(
                "Thank you i am Done ! please Upload the necessary docs and use 'stop or s' or  CTRL + C to Close me",
                reply_to_message_id=bot.message.message_id)

            while 1:
                await asyncio.sleep(5)
                # await browser.close()
    except KeyboardInterrupt:

        new_data = {"is_launched": False, "user_confirmed": False}
        await save_json(new_data)

    except Exception as e:
        new_data = {}
        new_data = {"is_launched": False, "user_confirmed": False}
        save_json(new_data)
        # await update.reply_text("ertyytrwerty")
        recent_message = await bot.message.reply_text(
            f"There is an error: {e}\npossibly your internet make sure your internet is good\nPlease restart with 'y' '",
            reply_to_message_id=bot.message.message_id)

        import traceback
        traceback.print_exc()

    except SystemExit as e:
        # Handle the SIGKILL signal here
        # Update JSON data to False
        print("HIII save by force ")
        new_data = {"is_launched": False, "user_confirmed": False}
        save_json(new_data)
    finally:
        import traceback
        traceback.print_exc()
        new_data = {"is_launched": False, "user_confirmed": False}
        save_json(new_data)
        print("HIII save by finally this is for the reasone! ")
        # settings_data = load_json(filename="settings.json")
        recent_message = await bot.message.reply_text(
            f"There is an error: {e}\npossibly your internet make sure your internet is good\nPlease restart with 'y' '",
            reply_to_message_id=bot.message.message_id)

# asyncio.run(main())

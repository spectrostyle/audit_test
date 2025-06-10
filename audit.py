from datetime import datetime, timedelta
import os
import PyPDF2
import csv
import shutil


def main():
    ax = ds = mc = vs = cc_total = 0
    project_dir = os.getcwd()
    audit_match = False

    # verify the template exists
    print("Starting Audit... \n")
    backup_check('SummaryTemplate.html', project_dir)

    # clean up old files
    file_cleanup(project_dir)

    # compare hotel values to processor values
    while audit_match is False:
        tr_hjs(project_dir)

        ax_hjs, ds_hjs, mc_hjs, vs_hjs = hjs_amounts()

        ax_tr, ds_tr, mc_tr, vs_tr, ax, ds, mc, vs, cc_total = tr_amounts()

        audit_match = compare(ax_hjs, ds_hjs, mc_hjs, vs_hjs,
                              ax_tr, ds_tr, mc_tr, vs_tr,
                              audit_match)

    # run processes on website manually
    input("Waiting for audit to run... (any button) \n")

    # start processes to fill out summary
    input("save FTC_NOheaders.csv and HS_headers.csv... (any button)\n")

    # pull values from needed sheets, ftc/hs
    ftc_hs(project_dir)
    print("\n")

    # adding values to sheet
    input("Update the Audit Summary? (any button)")
    room_revenue, cash, check = ftc_extractor()

    occupancy, ooo, rooms_sold, adr, mtd, ytd = hs_extractor()

    summary = update_summary(
        ax, ds, mc, vs, room_revenue, cash, check,
        occupancy, ooo, rooms_sold, adr, mtd, ytd,
        cc_total
    )
    print(f"{summary} created.")
    input("Any button to exit...")


# integrity check and file cleaner
def backup_check(backup, project_dir):
    backup_dir = os.path.join(project_dir, 'templateBackups')
    summary_template = os.path.join(backup_dir, backup)

    print(f"Checking if {backup} exists...")
    if not os.path.exists(summary_template):
        print(f"{backup} does not exist!")
        input(f"Obtain {backup} to update the summary!")
        exit()  # this portion is funny
    else:
        print(f"{backup} exists! \n")


# choice to wipe previously used files
def file_cleanup(project_dir):
    sheets_dir = os.path.join(project_dir, 'sheets')
    sheets_files = os.listdir(sheets_dir)

    clean = input("Wipe 'sheets' contents? (Y)/(N): ").lower().strip()
    if clean == 'y':
        for file_name in sheets_files:
            file_path = os.path.join(sheets_dir, file_name)
            try:
                os.remove(file_path)
            except FileNotFoundError:
                pass
        try:
            os.remove('Audit Summary.html')
        except FileNotFoundError:
            pass
        print("Files deleted. Starting TR | HJS search... \n")
    else:
        print("Keeping old files? Better be testing! \n")
        # no need to handle file not found as this is cleaning anyway?


# matching transaction report to hotel summary
def tr_hjs(project_dir):
    downloads_dir = os.path.expanduser('~\Downloads')
    audit_dir = os.path.join(project_dir, 'sheets')

    audit = ['hjs_headers.csv', 'tr.pdf']
    missing = []

    for needed in audit:
        if needed not in os.listdir(audit_dir):
            missing.append(needed)

    if missing:
        input("Checking Downloads folder for TR.pdf (TOTALS ONLY!!) and HJS_headers.csv... (any key)")

    while missing:
        for file in os.listdir(downloads_dir):
            if file == 'pdftrans.pdf':
                trans_report = 'tr.pdf'
                source_path = os.path.join(downloads_dir, file)
                destination_path = os.path.join(project_dir, 'sheets', trans_report)
                shutil.move(source_path, destination_path)
                print(f'{file} found; moved and renamed to {trans_report}')
                missing.remove('tr.pdf')
            elif file == 'report.csv':
                name_hjs = 'hjs_headers.csv'
                source_path = os.path.join(downloads_dir, file)
                destination_path = os.path.join(project_dir, 'sheets', name_hjs)
                shutil.move(source_path, destination_path)
                print(f'{file} found; moved and renamed to {name_hjs}')
                missing.remove('hjs_headers.csv')
            elif not missing:
                break

    print("TR, HJS found!")
    input("\n Ready to compare values? (any button)")
    print("\n" * 5)


# gets the daily value for each CC; AX needs the weird characters!
def hjs_amounts():
    ax_hjs = ds_hjs = mc_hjs = vs_hjs = 0

    with open('sheets/hjs_headers.csv', newline='') as csvfile:
        reader = csv.reader(csvfile)

        for row in reader:
            if row and row[0] in 'ï»¿"AX"':
                ax_hjs = row[4]
            elif row and row[0] in 'DS':
                ds_hjs = row[4]
            elif row and row[0] in 'MC':
                mc_hjs = row[4]
            elif row and row[0] in 'VI':
                vs_hjs = row[4]

    ax_hjs = value_cleaner(ax_hjs)
    ds_hjs = value_cleaner(ds_hjs)
    mc_hjs = value_cleaner(mc_hjs)
    vs_hjs = value_cleaner(vs_hjs)

    print("***HJS***" * 2)
    print(f"AX: ${ax_hjs:.2f}", f"DS: ${ds_hjs:.2f}",
          f"MC: ${mc_hjs:.2f}", f"VS: ${vs_hjs:.2f}", "\n", sep='\n')

    return ax_hjs, ds_hjs, mc_hjs, vs_hjs


def tr_amounts():
    tr_dir = 'sheets/tr.pdf'
    ax = ds = mc = vs = 0
    text = ''
    with open(tr_dir, 'rb'):
        reader = PyPDF2.PdfReader(tr_dir)
        for page_num in range(len(reader.pages)):
            text += reader.pages[page_num].extract_text()
    lines = text.split('\n')

    for line in lines:
        if line.startswith('AX'):
            ax = line.split()[-1]
        elif line.startswith('NS'):
            ds = line.split()[-1]
        elif line.startswith('MC'):
            mc = line.split()[-1]
        elif line.startswith('VS'):
            vs = line.split()[-1]

    ax_tr = ax = value_cleaner(ax)
    ds_tr = ds = value_cleaner(ds)
    mc_tr = mc = value_cleaner(mc)
    vs_tr = vs = value_cleaner(vs)
    # breakpoint here for negatives
    cc_total = str('${:,.2f}'.format(ax_tr+ds_tr+mc_tr+vs_tr))

    print("***TR***" * 2)
    print(f"AX: ${ax_tr:.2f}", f"DS: ${ds_tr:.2f}",
          f"MC: ${mc_tr:.2f}", f"VS: ${vs_tr:.2f}", "\n", sep='\n')
    return ax_tr, ds_tr, mc_tr, vs_tr, ax, ds, mc, vs, cc_total


def compare(ax_hjs, ds_hjs, mc_hjs, vs_hjs, ax_tr,  ds_tr, mc_tr, vs_tr, audit_match):
    bad_match = []

    if ax_hjs != ax_tr:
        print("Amex does not match")
        bad_match.append(f'Amex: {ax_hjs} | {ax_tr}')
    if ds_hjs != ds_tr:
        print("Discover does not match")
        bad_match.append(f'Discover: {ds_hjs} | {ds_tr}')
    if mc_hjs != mc_tr:
        print("Master Card does not match")
        bad_match.append(f'Master: {mc_hjs} | {mc_tr}')
    if vs_hjs != vs_tr:
        print("Visa does not match")
        bad_match.append(f'Visa: {vs_hjs} | {vs_tr}')

    if bad_match:   # feels messy, want to add lines below, but too much for too little?
        audit_match = False
        print("\n!!!!!BAD MATCH, FIX BEFORE AUDIT!!!!!\n")
        for pair in bad_match:
            print(pair)
        input("\nReady to verify TR | HJS again? (any key)")
        print("")
        bad_match.clear()
        return audit_match

    else:
        audit_match = True
        print("HJS *is equal to* TR! \n"
              "Audit is safe to run! \n")
        return audit_match


def ftc_hs(project_dir):
    audit = ['ftc_NOheaders.csv', 'hs_headers.csv']
    missing = []

    downloads_dir = os.path.expanduser('~\Downloads')
    audit_dir = os.path.join(project_dir, 'sheets')

    for file in audit:
        if file not in os.listdir(audit_dir):
            missing.append(file)
    for miss in missing:
        print(f"Missing: {miss}")

    while missing:
        input(f"Check Downloads folder for {missing}?")
        for file in os.listdir(downloads_dir):
            if file.endswith('.csv'):
                with open(os.path.join(downloads_dir, file), 'r', newline='') as csvfile:
                    csv_reader = csv.reader(csvfile)
                    line_count = 0
                    for row in csv_reader:
                        line_count += 1
                if line_count == 2:
                    name_hs = 'hs_headers.csv'
                    source_path = os.path.join(downloads_dir, file)
                    destination_path = os.path.join(project_dir, 'sheets', name_hs)
                    shutil.move(source_path, destination_path)
                    print(f'{file} found, moved and renamed to {name_hs}')
                    missing.remove('hs_headers.csv')
                elif line_count == 20 or line_count == 21:
                    name_ftc = 'ftc_NOheaders.csv'
                    source_path = os.path.join(downloads_dir, file)
                    destination_path = os.path.join(project_dir, 'sheets', name_ftc)
                    shutil.move(source_path, destination_path)
                    print(f'{file} found, moved and renamed to {name_ftc}')
                    missing.remove('ftc_NOheaders.csv')


def ftc_extractor():
    room_revenue = cash = check = 0
    with open('sheets/ftc_NOheaders.csv', newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if row and row[0] in 'Room Charge (RM)':
                room_revenue = row[4]
            elif row and row[0] in 'Cash (CA)':
                cash = row[4]
            elif row and row[0] in 'Check (CK)':
                check = row[4]
    cash = value_cleaner(cash)
    return room_revenue, cash, check


def hs_extractor():
    # no-headers mayhaps
    with open('sheets/hs_headers.csv', newline='') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        second_row = next(reader)
    # indexes of values needed
    occupancy = second_row[48]
    ooo = second_row[2]
    rooms_sold = second_row[13]
    adr = second_row[49]
    mtd = second_row[112]
    ytd = second_row[114]
    return occupancy, ooo, rooms_sold, adr, mtd, ytd


def update_summary(ax, ds, mc, vs, room_revenue, cash, check, occupancy, ooo, rooms_sold, adr, mtd, ytd, cc_total):

    current_time = datetime.now()
    audit_date = current_time - timedelta(days=1)
    weekday = audit_date.strftime("%A")
    month = audit_date.strftime("%m")
    day = audit_date.strftime("%d")
    year = audit_date.strftime("%Y")

    audit_date = f"{weekday} {month}/{day}/{year}"

    summary = 'Audit Summary.html'

    empty = '0.00'

    with open('templateBackups/SummaryTemplate.html', 'r', encoding='utf-8') as f:
        audit_summary = f.read()
        new_summary = audit_summary.replace('Day &amp; Date:', f'Day &amp; Date: {audit_date}'
                                  ).replace('Rooms Sold:', f'Rooms Sold: {rooms_sold}'
                                  ).replace('Occupancy: %', f'Occupancy: {occupancy}'
                                  ).replace('Out of Order Rooms:', f'Out of Order Rooms: {ooo}'
                                  ).replace('ADR: $', f'ADR: $ {adr}'
                                  ).replace('Room Revenue: $', f'Room Revenue: $ {room_revenue}'
                                  ).replace('Cash: $', f'Cash: $ {cash:.2f}'
                                  ).replace('AMEX: $', f'AMEX: $ {ax:.2f}'
                                  ).replace('Check: $', f'Check: $ {check}'
                                  ).replace('Discover(NS): $', f'Discover(NS): $ {ds:.2f}'
                                  ).replace('Guest Refund: $', f'Guest Refund: $ {empty}'
                                  ).replace('Mastercard: $', f'Mastercard: $ {mc:.2f}'
                                  ).replace('Visa: $', f'Visa: $ {vs:.2f}'
                                  ).replace('Credit Total: $', f'Credit Total: {cc_total}'
                                  ).replace('Month to Date: $', f'Month to Date: $ {mtd}'
                                  ).replace('Year to Date: $', f'Year to Date: $ {ytd}')

    with open(summary, 'w', encoding='utf-8') as f:
        f.write(new_summary)
        print('Audit Complete.')

    return summary


# function used to clean values ex: ($1,234.56) | 1234.56
def value_cleaner(value):
    # needing work here to hopefully catch the negatives
    if value:
        if value.startswith('(') or value:
            value = str(value)
            value = value.replace(",", "")
            value = value.strip("'[]$()")
            value = float(value)
        """else:
            value = str(value)
            value = value.replace(",", "")
            value = value.strip("'[]$")
            value = float(value)
            value = value - (value*2)"""
    else:
        value = 0
    return value


if __name__ == '__main__':
    main()

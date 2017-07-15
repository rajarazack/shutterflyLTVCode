import math, datetime,sys
from dateutil.parser import parse as date_parser

class LTV:
    def __init__(self):
        self.D = {}

    def ingest(self, e, D):
        self.D = D
        val = eval(e)

        # Converting the event_time to datetime format
        try:
            if 'event_time' in val:
                val['event_time'] = date_parser(val['event_time'])

            # Getting the customer_id from key if the type is CUSTOMER else getting it from customer_id if any other type
            if val['type'] == 'CUSTOMER':
                customer_id = val['key']
            else:
                customer_id = val['customer_id']

            # Storing the data into the dictionary D with customer_id as key and the entire line as the value
            # If the customer is new, a new dictionary row is created, else the same value is appended
            if customer_id not in D:
                self.D[customer_id] = [val]
            else:
                self.D[customer_id].append(val)
        except(ValueError, SyntaxError):
            print("DateFormat Error while parsing")
            print(val['customer_id'])

    def topXSimpleLTVCustomers(self, x, D):
        try:
            # SimpleLTV calculation
            resultLTV = []
            for customer_id in D:

                # Calculating the number of visits per week
                # Checking if the customer has SITE_VISIT to get event_time, else taking the ORDER event_time
                if 'SITE_VISIT' in [rec['type'] for rec in D[customer_id]]:
                    visitororder = 'SITE_VISIT'
                else:
                    visitororder = 'ORDER'
                # Getting a list of event times for the customer based on SITE_VISIT, if not ORDER
                visits_list = [rec['event_time'] for rec in D[customer_id] if rec['type'] == visitororder]

                # Checking if the customer visited the site and made orders, else just adding 0 as LTV for customer
                if visits_list and 'ORDER' in [rec['type'] for rec in D[customer_id]]:
                    # Calculating the count of weeks customer visited the site
                    start_date = min(visits_list)
                    end_date = max(visits_list)
                    # Considering week as between Monday-Sunday
                    # Getting corresponding Mondays for start and end date
                    start_date_monday = (start_date - datetime.timedelta(days=start_date.weekday()))
                    end_date_monday = (end_date - datetime.timedelta(days=end_date.weekday()))
                    # Adding 1 as days between does not account for end date
                    days_between = math.ceil((end_date_monday - start_date_monday).days)+1
                    # Adding 1 as count of weeks = weeks between dates + 1
                    active_week_count = int(days_between/ 7)+1

                    # Calculating the total revenue from the customer
                    # Collecting all the ORDER type records from the dictionary D for each customer_id
                    # Removing 'USD' from total_amount and conveerting it to float
                    order_records = [(rec['key'], rec['verb'], rec['event_time'], float(rec['total_amount'].split()[0]))
                                  for rec in self.D[customer_id] if rec['type'] == 'ORDER']
                    revenue_by_order_id = {}

                    # Checking for updates to orders based on event_time of orders
                    for order_id, verb, event_time, total_amount in order_records:
                        if order_id not in revenue_by_order_id:
                            revenue_by_order_id[order_id] = (event_time, total_amount)
                        else:
                            if event_time > revenue_by_order_id[order_id][0]:
                                revenue_by_order_id[order_id] = (event_time, total_amount)

                    # Adding up all the revenues for each customer
                    net_revenue = sum([revenue_by_order_id[order_id][1] for order_id in revenue_by_order_id])

                    # Average Weekly Revenue (a) = Total Revenue / Number of active weeks
                    a = float(net_revenue) / active_week_count

                    # Calculating LTV using the simple LTV formula:
                    # LTV = 52 weeks * Average Weekly Revenue (a) * customer lifespan (t)
                    t = 10
                    ltvresult = 52 * a * t
                    resultLTV.append((customer_id, ltvresult))
                else:
                    resultLTV.append((customer_id, 0))

            # Sort the customer, LTV list in descending order of LTV
            resultLTV.sort(key=lambda n: n[1], reverse=True)

            # Returning the top x rows of the customer, LTV list
            return resultLTV[:x]
        except:
            print("Unexpected error occured while processing customer_id")
            print(customer_id)


if __name__ == '__main__':

    # x is the top X number of customers needed
    x = 5
    input_file = "./input/input.txt"
    output_file = "./output/output.txt"
    ltv = LTV()
    data_dict = {}
    flag = 0
    # Reading each line from the input file to memory, line by line
    try:
        with open(input_file) as f:
            try:
                for l in f.readlines():
                    if flag == 0:
                        # First line, reading from second character to ignore '[' at the start and ',' at the end
                        line = l.strip()[1:-1]
                        flag = 1
                    else:
                        # Not the first line, reading from start and ignoring ',' or ']' at the end
                        line = l.strip()[:-1]
                    ltv.ingest(line, data_dict)
            except(SyntaxError):
                print("SyntaxError occured while parsing the input file in the following line:")
                print(l)
    except OSError:
        print("OS Error occured while opening input file")
    except:
        print("Unexpected error occured while opening output file")

    # LTV calculation
    top_LTV_Customers = ltv.topXSimpleLTVCustomers(x, data_dict)

    # Writing Top X LTV customers to output file
    try:
        with open(output_file, 'w') as f:
            for rec in top_LTV_Customers:
                f.write(rec[0] + ', ' + str(rec[1]) + '\n')
    except OSError:
        print("OS Error occured while opening output file")
    except:
        print("Unexpected error occured while opening output file")

    print "Output generated and saved in:"
    print output_file

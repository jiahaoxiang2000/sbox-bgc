from bitwuzla import *


# First, create a term manager instance.
tm = TermManager()
# Create a Bitwuzla options instance.
options = Options()
# Then, enable model generation.
options.set(Option.PRODUCE_MODELS, True)
# Create a Bitwuzla instance.
bitwuzla = Bitwuzla(tm, options)
bits = 4
bit_with = 2**bits
gate_number = 20
# XOR, AND, OR, NOT
gts = [0b0110, 0b001, 0b0111, 0b1100]
# this is the sbox, it is temp used, after need generate by the true sbox
xs = [0x00FF, 0x0F0F, 0x3333, 0x5555]
ys = [0x3B19, 0xCF50, 0x5707, 0x7174]

sortbv = tm.mk_bv_sort(bit_with)

# create the input and output variables
xs_v = [tm.mk_const(sortbv, "x{}".format(i)) for i in range(bits)]
ys_v = [tm.mk_const(sortbv, "y{}".format(i)) for i in range(bits)]

# create the constraints
for i in range(bits):
    bitwuzla.assert_formula(
        tm.mk_term(Kind.EQUAL, [xs_v[i], tm.mk_bv_value(sortbv, xs[i])])
    )
for i in range(bits):
    bitwuzla.assert_formula(
        tm.mk_term(Kind.EQUAL, [ys_v[i], tm.mk_bv_value(sortbv, ys[i])])
    )

# create the gate input and output
ts_v = [tm.mk_const(sortbv, "t{}".format(i)) for i in range(gate_number)]
qs_v = [tm.mk_const(sortbv, "q{}".format(i)) for i in range(gate_number * 2)]
# create the constraints for the input
for i in range(gate_number):
    input0 = [tm.mk_term(Kind.EQUAL, [qs_v[2 * i], xs_v[j]]) for j in range(bits)]
    input1 = [tm.mk_term(Kind.EQUAL, [qs_v[2 * i + 1], xs_v[j]]) for j in range(bits)]
    inter0 = [tm.mk_term(Kind.EQUAL, [qs_v[2 * i], ts_v[j]]) for j in range(i)]
    inter1 = [tm.mk_term(Kind.EQUAL, [qs_v[2 * i + 1], ts_v[j]]) for j in range(i)]
    bitwuzla.assert_formula(tm.mk_term(Kind.OR, input0 + inter0))
    bitwuzla.assert_formula(tm.mk_term(Kind.OR, input1 + inter1))

# need encoding for gate type
gts_v = [tm.mk_const(sortbv, "gt{}".format(i)) for i in range(gate_number)]

# create the constraints for the gate type
for i in range(gate_number):
    types = [
        tm.mk_term(Kind.EQUAL, [gts_v[i], tm.mk_bv_value(sortbv, gts[j])])
        for j in range(len(gts))
    ]
    bitwuzla.assert_formula(tm.mk_term(Kind.OR, types))

# create the constraints for the output, it is the hard part.
one_sort = tm.mk_bv_sort(1)
one = tm.mk_bv_value(one_sort, 1)
zores = tm.mk_bv_value(sortbv, 0)
ones = tm.mk_bv_value(sortbv, 2**bit_with - 1)
for i in range(gate_number):
    # create the constraints for the output
    gt0 = tm.mk_term(Kind.BV_EXTRACT, [gts_v[i]], [0, 0])
    gt1 = tm.mk_term(Kind.BV_EXTRACT, [gts_v[i]], [1, 1])
    gt2 = tm.mk_term(Kind.BV_EXTRACT, [gts_v[i]], [2, 2])
    gt3 = tm.mk_term(Kind.BV_EXTRACT, [gts_v[i]], [3, 3])
    gt0_ul = tm.mk_term(
        Kind.ITE,
        [
            tm.mk_term(Kind.BV_ULT, [gt0, one]),
            zores,
            tm.mk_term(Kind.BV_AND, [qs_v[2 * i], qs_v[2 * i + 1]]),
        ],
    )
    gt1_ul = tm.mk_term(
        Kind.ITE,
        [
            tm.mk_term(Kind.BV_ULT, [gt1, one]),
            zores,
            qs_v[2 * i + 1],
        ],
    )
    gt2_ul = tm.mk_term(
        Kind.ITE,
        [
            tm.mk_term(Kind.BV_ULT, [gt2, one]),
            zores,
            qs_v[2 * i],
        ],
    )
    gt3_ul = tm.mk_term(
        Kind.ITE,
        [
            tm.mk_term(Kind.BV_ULT, [gt3, one]),
            zores,
            ones,
        ],
    )
    bitwuzla.assert_formula(
        tm.mk_term(
            Kind.EQUAL,
            [
                ts_v[i],
                tm.mk_term(
                    Kind.BV_XOR,
                    [
                        gt0_ul,
                        tm.mk_term(
                            Kind.BV_XOR,
                            [gt1_ul, tm.mk_term(Kind.BV_XOR, [gt2_ul, gt3_ul])],
                        ),
                    ],
                ),
            ],
        )
    )
# create the constraints for the sbox output link the gate output
for i in range(bits):
    ts_temp = [tm.mk_term(Kind.EQUAL, [ys_v[i], ts_v[j]]) for j in range(gate_number)]
    bitwuzla.assert_formula(tm.mk_term(Kind.OR, ts_temp))

assertions = bitwuzla.get_assertions()
print("Assertions:")
print("{")
for a in assertions:
    print(f" {a}")
print("}")

if __name__ == "__main__":
    # Check the assertions
    result = bitwuzla.check_sat()
    print("Result:", result)
    if result == Result.SAT:
        model = bitwuzla.get_model()
        print("Model:")
        print("{")
        for d in model.decls():
            print(f" {d.name()} -> {model.get_value(d)}")
        print("}")

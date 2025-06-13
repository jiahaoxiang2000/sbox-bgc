(set-logic QF_BV)
(set-option :produce-models true)

(declare-const x0 (_ BitVec 4))
(declare-const x1 (_ BitVec 4))
(declare-const y0 (_ BitVec 4))
(declare-const y1 (_ BitVec 4))
(assert (= x0 #b0011))
(assert (= x1 #b0101))
(assert (= y0 #b0100))
(assert (= y1 #b0110))

(declare-const t0 (_ BitVec 4))
(declare-const t1 (_ BitVec 4))
(declare-const q0 (_ BitVec 4))
(declare-const q1 (_ BitVec 4))
(declare-const q2 (_ BitVec 4))
(declare-const q3 (_ BitVec 4))
(assert (or (= q0 x0) (= q0 x1)))
(assert (or (= q1 x0) (= q1 x1)))
(assert (or (= q2 x0) (= q2 x1) (= q2 t0)))
(assert (or (= q3 x0) (= q3 x1) (= q3 t0)))

(declare-const gt0 (_ BitVec 4))
(declare-const gt1 (_ BitVec 4))
(assert (or (= gt0 #b0110) (= gt0 #b0001) ) )
(assert (or (= gt1 #b0110) (= gt1 #b0001) ) )

(assert (= (bvxor (bvxor (bvxor (ite (bvult ((_ extract 0 0) gt0) #b1) #b0000 (bvand q0 q1)) (ite (bvult ((_ extract 1 1) gt0) #b1) #b0000 q1)) (ite (bvult ((_ extract 2 2) gt0) #b1) #b0000 q0)) (ite (bvult ((_ extract 3 3) gt0) #b1) #b0000 #b1111)) t0))

(assert (= (bvxor (bvxor (bvxor (ite (bvult ((_ extract 0 0) gt1) #b1) #b0000 (bvand q2 q3)) (ite (bvult ((_ extract 1 1) gt1) #b1) #b0000 q3)) (ite (bvult ((_ extract 2 2) gt1) #b1) #b0000 q2)) (ite (bvult ((_ extract 3 3) gt1) #b1) #b0000 #b1111)) t1))

(assert (or (= y0 t0) (= y0 t1)))
(assert (or (= y1 t0) (= y1 t1)))

(check-sat)
(get-model)

(exit)
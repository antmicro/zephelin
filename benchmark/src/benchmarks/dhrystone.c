/*  Author:     Reinhold P. Weicker
 *              Siemens Nixdorf, Paderborn/Germany
 *              weicker@specbench.org
 *  Date:       May 25, 1988
 *  Modified:	Steven Pemberton, CWI, Amsterdam; Steven.Pemberton@cwi.nl
 *  Date:       October, 1993; March 1995
 *              Included both files into one source, that gets compiled
 *              in two passes. Made program auto-compiling, and auto-running,
 *              and generally made it much easier to use.
 *
 *              Original Version (in Ada) published in
 *              "Communications of the ACM" vol. 27., no. 10 (Oct. 1984),
 *              pp. 1013 - 1030, together with the statistics
 *              on which the distribution of statements etc. is based.
 *
 *              In this C version, the following C library functions are used:
 *              - strcpy, strcmp (inside the measurement loop)
 *              - printf, scanf (outside the measurement loop)
 *              In addition, Berkeley UNIX system calls "times ()" or "time ()"
 *              are used for execution time measurement. For measurements
 *              on other systems, these calls have to be changed.
 *  Modified:	Analog Devices, Inc; Antmicro <www.antmicro.com>
 *  Date:		April, 2026
 */

#include <bench.h>

#include <stdio.h>
#include <string.h>
/* for strcpy, strcmp */

#define Null  0
/* Value of a Null pointer */
#define true  1
#define false 0

typedef int One_Thirty;
typedef int One_Fifty;
typedef char Capital_Letter;
typedef int Boolean;
typedef char Str_30[31];
typedef int Arr_1_Dim[50];
typedef int Arr_2_Dim[50][50];

#define structassign(d, s) d = s

typedef enum {
	Ident_1,
	Ident_2,
	Ident_3,
	Ident_4,
	Ident_5
} Enumeration;

typedef struct record {
	struct record *Ptr_Comp;
	Enumeration Discr;
	union {
		struct {
			Enumeration Enum_Comp;
			int Int_Comp;
			char Str_Comp[31];
		} var_1;
		struct {
			Enumeration E_Comp_2;
			char Str_2_Comp[31];
		} var_2;
		struct {
			char Ch_1_Comp;
			char Ch_2_Comp;
		} var_3;
	} variant;
} Rec_Type, *Rec_Pointer;

Rec_Pointer Ptr_Glob, Next_Ptr_Glob;
int Int_Glob;
Boolean Bool_Glob;
char Ch_1_Glob, Ch_2_Glob;
int Arr_1_Glob[50];
int Arr_2_Glob[50][50];

long Begin_Time, End_Time, User_Time;

One_Fifty Int_1_Loc;
One_Fifty Int_2_Loc;
One_Fifty Int_3_Loc;
char Ch_Index;
Enumeration Enum_Loc;
Str_30 Str_1_Loc;
Str_30 Str_2_Loc;
int Run_Index;

void Proc_1(Rec_Pointer Ptr_Val_Par);
void Proc_2(One_Fifty *Int_Par_Ref);
void Proc_3(Rec_Pointer *Ptr_Ref_Par);
void Proc_4(void);
void Proc_5(void);
void Proc_6(Enumeration Enum_Val_Par, Enumeration *Enum_Ref_Par);
void Proc_7(One_Fifty Int_1_Par_Val, One_Fifty Int_2_Par_Val, One_Fifty *Int_Par_Ref);
void Proc_8(Arr_1_Dim Arr_1_Par_Ref, Arr_2_Dim Arr_2_Par_Ref, int Int_1_Par_Val, int Int_2_Par_Val);
Enumeration Func_1(Capital_Letter Ch_1_Par_Val, Capital_Letter Ch_2_Par_Val);
Boolean Func_2(Str_30 Str_1_Par_Ref, Str_30 Str_2_Par_Ref);
Boolean Func_3(Enumeration Enum_Par_Val);

void dhrystone_run(void)
{
	Proc_5();
	Proc_4();
	/* Ch_1_Glob == 'A', Ch_2_Glob == 'B', Bool_Glob == true */
	Int_1_Loc = 2;
	Int_2_Loc = 3;
	strcpy(Str_2_Loc, "DHRYSTONE PROGRAM, 2'ND STRING");
	Enum_Loc = Ident_2;
	Bool_Glob = !Func_2(Str_1_Loc, Str_2_Loc);
	/* Bool_Glob == 1 */

	while (Int_1_Loc < Int_2_Loc) {
		Int_3_Loc = 5 * Int_1_Loc - Int_2_Loc;
		/* Int_3_Loc == 7 */
		Proc_7(Int_1_Loc, Int_2_Loc, &Int_3_Loc);
		/* Int_3_Loc == 7 */
		Int_1_Loc += 1;
	}
	/* Int_1_Loc == 3, Int_2_Loc == 3, Int_3_Loc == 7 */

	Proc_8(Arr_1_Glob, Arr_2_Glob, Int_1_Loc, Int_3_Loc);
	/* Int_Glob == 5 */
	Proc_1(Ptr_Glob);

	for (Ch_Index = 'A'; Ch_Index <= Ch_2_Glob; ++Ch_Index) {
		if (Enum_Loc == Func_1(Ch_Index, 'C')) {
			Proc_6(Ident_1, &Enum_Loc);
			strcpy(Str_2_Loc, "DHRYSTONE PROGRAM, 3'RD STRING");
			Int_2_Loc = Run_Index;
			Int_Glob = Run_Index;
		}
	}
	/* Int_1_Loc == 3, Int_2_Loc == 3, Int_3_Loc == 7 */
	Int_2_Loc = Int_2_Loc * Int_1_Loc;
	Int_1_Loc = Int_2_Loc / Int_3_Loc;
	Int_2_Loc = 7 * (Int_2_Loc - Int_3_Loc) - Int_1_Loc;
	/* Int_1_Loc == 1, Int_2_Loc == 13, Int_3_Loc == 7 */
	Proc_2(&Int_1_Loc);
	/* Int_1_Loc == 5 */
}

void benchmark_setup(void)
{
	static Rec_Type Next_Ptr_Glob_s, Ptr_Glob_s;

	Next_Ptr_Glob = (Rec_Pointer)&Next_Ptr_Glob_s;
	Ptr_Glob = (Rec_Pointer)&Ptr_Glob_s;

	Ptr_Glob->Ptr_Comp = Next_Ptr_Glob;
	Ptr_Glob->Discr = Ident_1;
	Ptr_Glob->variant.var_1.Enum_Comp = Ident_3;
	Ptr_Glob->variant.var_1.Int_Comp = 40;
	strcpy(Ptr_Glob->variant.var_1.Str_Comp, "DHRYSTONE PROGRAM, SOME STRING");
	strcpy(Str_1_Loc, "DHRYSTONE PROGRAM, 1'ST STRING");

	Arr_2_Glob[8][7] = 10;
}

void benchmark_teardown(void)
{
	fprintf(stderr, "Final values of the variables used in the benchmark:\n");
	fprintf(stderr, "\n");
	fprintf(stderr, "Int_Glob:            %d\n", Int_Glob);
	fprintf(stderr, "        should be:   %d\n", 5);
	fprintf(stderr, "Bool_Glob:           %d\n", Bool_Glob);
	fprintf(stderr, "        should be:   %d\n", 1);
	fprintf(stderr, "Ch_1_Glob:           %c\n", Ch_1_Glob);
	fprintf(stderr, "        should be:   %c\n", 'A');
	fprintf(stderr, "Ch_2_Glob:           %c\n", Ch_2_Glob);
	fprintf(stderr, "        should be:   %c\n", 'B');
	fprintf(stderr, "Arr_1_Glob[8]:       %d\n", Arr_1_Glob[8]);
	fprintf(stderr, "        should be:   %d\n", 7);
	fprintf(stderr, "Arr_2_Glob[8][7]:    %d\n", Arr_2_Glob[8][7]);
	fprintf(stderr, "        should be:   Number_Of_Runs + 10\n");
	fprintf(stderr, "Ptr_Glob->\n");
	fprintf(stderr, "  Ptr_Comp:          %d\n", (int)Ptr_Glob->Ptr_Comp);
	fprintf(stderr, "        should be:   (implementation-dependent)\n");
	fprintf(stderr, "  Discr:             %d\n", Ptr_Glob->Discr);
	fprintf(stderr, "        should be:   %d\n", 0);
	fprintf(stderr, "  Enum_Comp:         %d\n", Ptr_Glob->variant.var_1.Enum_Comp);
	fprintf(stderr, "        should be:   %d\n", 2);
	fprintf(stderr, "  Int_Comp:          %d\n", Ptr_Glob->variant.var_1.Int_Comp);
	fprintf(stderr, "        should be:   %d\n", 17);
	fprintf(stderr, "  Str_Comp:          %s\n", Ptr_Glob->variant.var_1.Str_Comp);
	fprintf(stderr, "        should be:   DHRYSTONE PROGRAM, SOME STRING\n");
	fprintf(stderr, "Next_Ptr_Glob->\n");
	fprintf(stderr, "  Ptr_Comp:          %d\n", (int)Next_Ptr_Glob->Ptr_Comp);
	fprintf(stderr, "        should be:   (implementation-dependent), same as above\n");
	fprintf(stderr, "  Discr:             %d\n", Next_Ptr_Glob->Discr);
	fprintf(stderr, "        should be:   %d\n", 0);
	fprintf(stderr, "  Enum_Comp:         %d\n", Next_Ptr_Glob->variant.var_1.Enum_Comp);
	fprintf(stderr, "        should be:   %d\n", 1);
	fprintf(stderr, "  Int_Comp:          %d\n", Next_Ptr_Glob->variant.var_1.Int_Comp);
	fprintf(stderr, "        should be:   %d\n", 18);
	fprintf(stderr, "  Str_Comp:          %s\n", Next_Ptr_Glob->variant.var_1.Str_Comp);
	fprintf(stderr, "        should be:   DHRYSTONE PROGRAM, SOME STRING\n");
	fprintf(stderr, "Int_1_Loc:           %d\n", Int_1_Loc);
	fprintf(stderr, "        should be:   %d\n", 5);
	fprintf(stderr, "Int_2_Loc:           %d\n", Int_2_Loc);
	fprintf(stderr, "        should be:   %d\n", 13);
	fprintf(stderr, "Int_3_Loc:           %d\n", Int_3_Loc);
	fprintf(stderr, "        should be:   %d\n", 7);
	fprintf(stderr, "Enum_Loc:            %d\n", Enum_Loc);
	fprintf(stderr, "        should be:   %d\n", 1);
	fprintf(stderr, "Str_1_Loc:           %s\n", Str_1_Loc);
	fprintf(stderr, "        should be:   DHRYSTONE PROGRAM, 1'ST STRING\n");
	fprintf(stderr, "Str_2_Loc:           %s\n", Str_2_Loc);
	fprintf(stderr, "        should be:   DHRYSTONE PROGRAM, 2'ND STRING\n");
	fprintf(stderr, "\n");
}

void benchmark_run(void)
{
	dhrystone_run();
}

void Proc_1(Rec_Pointer Ptr_Val_Par)
{
	Rec_Pointer Next_Record = Ptr_Val_Par->Ptr_Comp;
	/* == Ptr_Glob_Next */
	/* Local variable, initialized with Ptr_Val_Par->Ptr_Comp,    */
	/* corresponds to "rename" in Ada, "with" in Pascal           */

	structassign(*Ptr_Val_Par->Ptr_Comp, *Ptr_Glob);
	Ptr_Val_Par->variant.var_1.Int_Comp = 5;
	Next_Record->variant.var_1.Int_Comp = Ptr_Val_Par->variant.var_1.Int_Comp;
	Next_Record->Ptr_Comp = Ptr_Val_Par->Ptr_Comp;

	Proc_3(&Next_Record->Ptr_Comp);

	/* Ptr_Val_Par->Ptr_Comp->Ptr_Comp
						== Ptr_Glob->Ptr_Comp */
	if (Next_Record->Discr == Ident_1) {
		Next_Record->variant.var_1.Int_Comp = 6;
		Proc_6(Ptr_Val_Par->variant.var_1.Enum_Comp, &Next_Record->variant.var_1.Enum_Comp);
		Next_Record->Ptr_Comp = Ptr_Glob->Ptr_Comp;
		Proc_7(Next_Record->variant.var_1.Int_Comp, 10,
		       &Next_Record->variant.var_1.Int_Comp);
	} else {
		structassign(*Ptr_Val_Par, *Ptr_Val_Par->Ptr_Comp);
	}
}

void Proc_2(One_Fifty *Int_Par_Ref)
{
	One_Fifty Int_Loc;
	Enumeration Enum_Loc;

	Int_Loc = *Int_Par_Ref + 10;
	do {
		if (Ch_1_Glob == 'A') {
			Int_Loc -= 1;
			*Int_Par_Ref = Int_Loc - Int_Glob;
			Enum_Loc = Ident_1;
		}
	} while (Enum_Loc != Ident_1);
}

void Proc_3(Rec_Pointer *Ptr_Ref_Par)
{
	if (Ptr_Glob != Null) {
		*Ptr_Ref_Par = Ptr_Glob->Ptr_Comp;
	}
	Proc_7(10, Int_Glob, &Ptr_Glob->variant.var_1.Int_Comp);
}

void Proc_4(void)
{
	Boolean Bool_Loc;

	Bool_Loc = Ch_1_Glob == 'A';
	Bool_Glob = Bool_Loc | Bool_Glob;
	Ch_2_Glob = 'B';
}

void Proc_5(void)
{
	Ch_1_Glob = 'A';
	Bool_Glob = false;
}
void Proc_6(Enumeration Enum_Val_Par, Enumeration *Enum_Ref_Par)
{
	*Enum_Ref_Par = Enum_Val_Par;
	if (!Func_3(Enum_Val_Par)) {
		*Enum_Ref_Par = Ident_4;
	}
	switch (Enum_Val_Par) {
	case Ident_1:
		*Enum_Ref_Par = Ident_1;
		break;
	case Ident_2:
		if (Int_Glob > 100) {
			*Enum_Ref_Par = Ident_1;
		} else {
			*Enum_Ref_Par = Ident_4;
		}
		break;
	case Ident_3:
		*Enum_Ref_Par = Ident_2;
		break;
	case Ident_4:
		break;
	case Ident_5:
		*Enum_Ref_Par = Ident_3;
		break;
	}
}

void Proc_7(One_Fifty Int_1_Par_Val, One_Fifty Int_2_Par_Val, One_Fifty *Int_Par_Ref)
{
	One_Fifty Int_Loc;

	Int_Loc = Int_1_Par_Val + 2;
	*Int_Par_Ref = Int_2_Par_Val + Int_Loc;
}

void Proc_8(Arr_1_Dim Arr_1_Par_Ref, Arr_2_Dim Arr_2_Par_Ref, int Int_1_Par_Val, int Int_2_Par_Val)
{
	One_Fifty Int_Index;
	One_Fifty Int_Loc;

	Int_Loc = Int_1_Par_Val + 5;
	Arr_1_Par_Ref[Int_Loc] = Int_2_Par_Val;
	Arr_1_Par_Ref[Int_Loc + 1] = Arr_1_Par_Ref[Int_Loc];
	Arr_1_Par_Ref[Int_Loc + 30] = Int_Loc;
	for (Int_Index = Int_Loc; Int_Index <= Int_Loc + 1; ++Int_Index) {
		Arr_2_Par_Ref[Int_Loc][Int_Index] = Int_Loc;
	}
	Arr_2_Par_Ref[Int_Loc][Int_Loc - 1] += 1;
	Arr_2_Par_Ref[Int_Loc + 20][Int_Loc] = Arr_1_Par_Ref[Int_Loc];
	Int_Glob = 5;
}

Enumeration Func_1(Capital_Letter Ch_1_Par_Val, Capital_Letter Ch_2_Par_Val)
{
	Capital_Letter Ch_1_Loc;
	Capital_Letter Ch_2_Loc;

	Ch_1_Loc = Ch_1_Par_Val;
	Ch_2_Loc = Ch_1_Loc;
	if (Ch_2_Loc != Ch_2_Par_Val) {
		return Ident_1;
	} else {
		Ch_1_Glob = Ch_1_Loc;
		return Ident_2;
	}
}

Boolean Func_2(Str_30 Str_1_Par_Ref, Str_30 Str_2_Par_Ref)
{
	One_Thirty Int_Loc;
	Capital_Letter Ch_Loc;

	Int_Loc = 2;
	while (Int_Loc <= 2) {
		if (Func_1(Str_1_Par_Ref[Int_Loc], Str_2_Par_Ref[Int_Loc + 1]) == Ident_1) {
			Ch_Loc = 'A';
			Int_Loc += 1;
		}
	}
	if (Ch_Loc >= 'W' && Ch_Loc < 'Z') {
		Int_Loc = 7;
	}
	if (Ch_Loc == 'R') {
		return true;
	} else {
		if (strcmp(Str_1_Par_Ref, Str_2_Par_Ref) > 0) {
			Int_Loc += 7;
			Int_Glob = Int_Loc;
			return true;
		} else {
			return false;
		}
	}
}

Boolean Func_3(Enumeration Enum_Par_Val)
{
	Enumeration Enum_Loc;

	Enum_Loc = Enum_Par_Val;
	if (Enum_Loc == Ident_3) {
		/* then, executed */
		return true;
	} else { /* not executed */
		return false;
	}
}

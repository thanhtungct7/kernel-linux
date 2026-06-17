#include <linux/module.h>
#include <linux/moduleparam.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/stat.h>

/* ── forward declarations ── */
int factorial(int n);
int matadd(int p, int q, int *a, int *b, int *c);
int matmul(int p, int q, int s, int *a, int *b, int *c);
int primeBetween(int m, int n);
int smallernuminmatrix(int p, int q, int *a, int s);
int numdivisibleinmatrix(int p, int q, int *a, int s);
int primeofmat(int p, int q, int *a);
int prime(int n);

/* ── module parameters ── */
static int choice = 0;
static int p, q, s, d;
static int a[2500], b[2500], c[2500];

module_param(choice, int, S_IRUGO);
module_param(d, int, S_IRUGO);
module_param(p, int, S_IRUGO);
module_param(q, int, S_IRUGO);
module_param(s, int, S_IRUGO);
module_param_array(a, int, NULL, S_IRUGO);
module_param_array(b, int, NULL, S_IRUGO);

static int p02_init(void)
{
	switch (choice) {
	case 1:
		printk(KERN_ALERT "\n%d! = %d\n", d, factorial(d));
		break;
	case 2:
		matadd(p, q, a, b, c);
		break;
	case 3:
		matmul(p, q, s, a, b, c);
		break;
	case 4:
		primeBetween(p, s);
		break;
	case 5:
		smallernuminmatrix(p, q, a, s);
		break;
	case 6:
		numdivisibleinmatrix(p, q, a, s);
		break;
	case 7:
		primeofmat(p, q, a);
		break;
	default:
		printk(KERN_ALERT "Invalid choice: %d\n", choice);
	}
	return 0;
}

/* ── case 1: giai thừa ── */
int factorial(int n)
{
	int gt = 1;
	int i;

	for (i = 2; i <= n; i++)
		gt *= i;
	return gt;
}

/* ── case 2: cộng ma trận ── */
int matadd(int p, int q, int *a, int *b, int *c)
{
	int i, j;

	for (i = 0; i < p; i++)
		for (j = 0; j < q; j++)
			c[i * q + j] = a[i * q + j] + b[i * q + j];

	printk(KERN_ALERT "\nSum of 2 matrices (%d x %d):\n", p, q);
	for (i = 0; i < p; i++) {
		for (j = 0; j < q; j++)
			printk(KERN_CONT "%-7d", c[i * q + j]);
		printk(KERN_CONT "\n");
	}
	return 0;
}

/* ── case 3: nhân ma trận ── */
int matmul(int p, int q, int s, int *a, int *b, int *c)
{
	int i, j, l;

	/* khởi tạo ma trận kết quả về 0 trước khi tích lũy */
	for (i = 0; i < p * s; i++)
		c[i] = 0;

	for (i = 0; i < p; i++)
		for (j = 0; j < s; j++)
			for (l = 0; l < q; l++)
				c[i * s + j] += a[i * q + l] * b[l * s + j];

	printk(KERN_ALERT "\nProduct of 2 matrices (%d x %d):\n", p, s);
	for (i = 0; i < p; i++) {
		for (j = 0; j < s; j++)
			printk(KERN_CONT "%-7d", c[i * s + j]);
		printk(KERN_CONT "\n");
	}
	return 0;
}

/* ── case 4: số nguyên tố trong khoảng (p, s) ── */
int primeBetween(int num1, int num2)
{
	int i, j, is_prime;

	printk(KERN_ALERT "\nPrimes between %d and %d:\n", num1, num2);
	for (i = num1 + 1; i < num2; i++) {
		is_prime = 1;
		for (j = 2; j * j <= i; j++) {
			if (i % j == 0) { is_prime = 0; break; }
		}
		if (is_prime && i > 1)
			printk(KERN_CONT "%d ", i);
	}
	printk(KERN_CONT "\n");
	return 0;
}

/* ── case 5: đếm số nhỏ hơn s ── */
int smallernuminmatrix(int p, int q, int *a, int s)
{
	int i, j, count = 0;

	for (i = 0; i < p; i++)
		for (j = 0; j < q; j++)
			if (a[i * q + j] < s)
				count++;

	printk(KERN_ALERT "There are %d numbers smaller than %d in this matrix\n",
	       count, s);
	return 0;
}

/* ── case 6: đếm số chia hết cho s ── */
int numdivisibleinmatrix(int p, int q, int *a, int s)
{
	int i, j, count = 0;

	if (s == 0) {
		printk(KERN_ALERT "Error: divisor s must not be 0\n");
		return -1;
	}
	for (i = 0; i < p; i++)
		for (j = 0; j < q; j++)
			if (a[i * q + j] % s == 0)
				count++;

	printk(KERN_ALERT "There are %d numbers divisible by %d in this matrix\n",
	       count, s);
	return 0;
}

/* ── case 7: đếm số nguyên tố trong ma trận ── */
int primeofmat(int p, int q, int *a)
{
	int i, j, count = 0;

	for (i = 0; i < p; i++)
		for (j = 0; j < q; j++)
			count += prime(a[i * q + j]);

	printk(KERN_ALERT "There are %d prime numbers in this matrix\n", count);
	return 0;
}

int prime(int n)
{
	int i;

	if (n <= 1) return 0;
	for (i = 2; i * i <= n; i++)
		if (n % i == 0) return 0;
	return 1;
}

static void p02_exit(void)
{
	printk(KERN_ALERT "Goodbye\n");
}

module_init(p02_init);
module_exit(p02_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("nhom");
MODULE_DESCRIPTION("Part 3 – math operations via kernel module params");

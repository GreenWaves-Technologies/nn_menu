#ifndef __measurments_utils_H__
#define __measurments_utils_H__

#if defined(GPIO_MEAS) && !defined(__EMUL__)
#ifdef __GAP9__
#define GPIO_MEAS_PIN PI_GPIO_A89
#else
#define GPIO_MEAS_PIN PI_GPIO_A02
#endif
struct pi_device gpio_meas_port;
pi_gpio_e gpio_meas_pin_o;
#define OPEN_GPIO_MEAS() \
  struct pi_gpio_conf gpio_conf = {0}; \
  gpio_meas_pin_o = GPIO_MEAS_PIN; /* PI_GPIO_A02-PI_GPIO_A05 */ \
  pi_gpio_conf_init(&gpio_conf); \
  pi_open_from_conf(&gpio_meas_port, &gpio_conf); \
  gpio_conf.port = (gpio_meas_pin_o & PI_GPIO_NUM_MASK) / 32; \
  int errors = pi_gpio_open(&gpio_meas_port); \
  if (errors) \
  { \
      printf("Error opening GPIO %d\n", errors); \
      pmsis_exit(errors); \
  } \
  pi_gpio_pin_configure(&gpio_meas_port, gpio_meas_pin_o, PI_GPIO_OUTPUT); \
  pi_gpio_pin_write(&gpio_meas_port, gpio_meas_pin_o, 0);

#define GPIO_HIGH() pi_gpio_pin_write(&gpio_meas_port, gpio_meas_pin_o, 1)
#define GPIO_LOW()  pi_gpio_pin_write(&gpio_meas_port, gpio_meas_pin_o, 0)
#else
#define OPEN_GPIO_MEAS()
#define GPIO_HIGH()
#define GPIO_LOW()
#endif

#endif
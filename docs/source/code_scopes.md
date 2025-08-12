# Tracing code scopes

Zeppelin allows for marking certain code scopes for tracing.
When the program execution enters an enabled scope, an event is emitted before and after the code is executed.
The scopes can be enabled and disabled at both build-time and runtime.

## Marking the code

### Defining the scopes

To use the scopes in code, first define the scopes using the `ZPL_CODE_SCOPE_DEFINE` macro.

```c
// ZPL_CODE_SCOPE_DEFINE(name, is_enabled);
ZPL_CODE_SCOPE_DEFINE(code_scope_name_1, false);
ZPL_CODE_SCOPE_DEFINE(code_scope_name_2, true);
```

The first parameter is the code scope name, that will be used as a handle for marking the code scopes.
The second parameter, `is_enabled` flag, describes the initial state of the scope.
The scope can be enabled or disabled at boot, but it can always be switched at runtime.

### Marking the code using `ZPL_MARK_CODE_SCOPE`

To mark the desired code scopes, Zeppelin provides a special macro.
The scope event will be emitted before and after the code inside is executed.
The macro takes in one parameter, which is the name of the scope defined earlier using the `ZPL_CODE_SCOPE_DEFINE` macro.

```c
ZPL_MARK_CODE_SCOPE(code_scope_name) {
    // ... Code inside the code scope
}
```

### Marking the code using functions

Alternatively you can mark the scopes using the enter/exit functions.
Those functions work exactly the same as the macro showcased above.

```c
zpl_code_scope_enter(code_scope_name);
// ... Code inside the code scope
zpl_code_scope_exit(code_scope_name);
```

This method allows for the entry and exit to be defined in separate contexts.
For example you can mark the beginning of a scope in one function, and the ending in a different function.

```c
void start_function(void)
{
    zpl_code_scope_enter(code_scope_name);
    // Function body
}

void end_function(void)
{
    // Function body
    zpl_code_scope_exit(code_scope_name);
}
```

### Example

In the example below, two scopes are created.
Both methods (macro and function) uses are showcased here.
Marking the code scopes in both ways results in the same behavior.

```c
#include <zpl/lib.h>

ZPL_CODE_SCOPE_DEFINE(code_scope1, false);
ZPL_CODE_SCOPE_DEFINE(code_scope2, true);

int main(void)
{
    zpl_init();

    ZPL_MARK_CODE_SCOPE(code_scope1) {
        // ... Code inside code_scope1
    }

    zpl_code_scope_enter(code_scope2);
    // ... Code inside code_scope2
    zpl_code_scope_exit(code_scope2);

    return 0;
}
```

## Enabling/disabling code scopes at runtime

Code scopes can be enabled and disabled at runtime.
This can be done two ways, via UART shell, or by changing the scope's state in memory.

### UART runtime configuration

To use the UART runtime configuration, enable the `CONFIG_ZPL_RUNTIME_CONFIG_UART` Kconfig option.

To list available configs and their current state, use the command `dynamic_conf list`:

```
uart:~$ dynamic_conf list
Available configs:
 code_scope1: disabled
 code_scope2: disabled
 code_scope3: enabled
 code_scope4: enabled
```

To change state of the scope use `dynamic_conf enable <scope>` to enable and `dynamic_conf disable <scope>` to disable the scopes:

```
uart:~$ dynamic_conf enable code_scope1
uart:~$ dynamic_conf disable code_scope4
```

### Debug runtime configuration

Code scopes can also be enabled directly in memory for example by using GDB.
If the binary has been build with debug symbols, then in GDB you can access them by name.

To check the state of a code scope, in GDB enter:

```
>>> print code_scope1.is_enabled
$1 = false
```

To change the state of a scope:

```
>>> set var code_scope1.is_enabled=1
>>> set var code_scope2.is_enabled=0
```

// void_pointer_demo.cpp
// Comprehensive void* demonstration with modern C++ best practices
//
// Compile: g++ -std=c++17 -Wall -Wextra -Wpedantic void_pointer_demo.cpp -o void_demo

#include <cassert>
#include <cstddef>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <type_traits>
#include <utility>
#include <variant>
#include <vector>

namespace voidptr_demo {

// ============================================================
// 1. Generic swap with exception safety
// ============================================================
void generic_swap(void* a, void* b, std::size_t size) {
    if (!a || !b) throw std::invalid_argument("generic_swap: null pointer");
    if (a == b) return; // no-op

    constexpr std::size_t kStackThreshold = 256;
    std::byte stack_buf[kStackThreshold];
    std::byte* buf = stack_buf;
    std::unique_ptr<std::byte[]> heap_buf;

    if (size > kStackThreshold) {
        heap_buf = std::make_unique<std::byte[]>(size);
        buf = heap_buf.get();
    }

    std::memcpy(buf, a, size);
    std::memcpy(a, b, size);
    std::memcpy(b, buf, size);
    // heap_buf automatically cleaned up by unique_ptr
}

// ============================================================
// 2. Type-tagged generic print with validation
// ============================================================
enum class TypeTag : int { Int, Double, CString };

void generic_print(const void* data, TypeTag tag) {
    if (!data) throw std::invalid_argument("generic_print: null data");
    
    switch (tag) {
        case TypeTag::Int:
            std::cout << "int:    " << *static_cast<const int*>(data) << '\n';
            break;
        case TypeTag::Double:
            std::cout << "double: " << *static_cast<const double*>(data) << '\n';
            break;
        case TypeTag::CString:
            std::cout << "cstr:   " << static_cast<const char*>(data) << '\n';
            break;
        default:
            throw std::invalid_argument("generic_print: unknown tag");
    }
}

// ============================================================
// 3. Generic array reducer with const-correctness
// ============================================================
using Reducer = void* (*)(void* accum, const void* elem);

void* int_sum_reducer(void* accum, const void* elem) {
    *static_cast<int*>(accum) += *static_cast<const int*>(elem);
    return accum;
}

void reduce_array(void* accum,
                  const void* base,
                  std::size_t count,
                  std::size_t elem_size,
                  Reducer fn) {
    if (!fn) throw std::invalid_argument("reduce_array: null function");
    if (count > 0 && !base) throw std::invalid_argument("reduce_array: null base");

    const auto* p = static_cast<const std::byte*>(base);
    for (std::size_t i = 0; i < count; ++i) {
        fn(accum, p + i * elem_size);
    }
}

// ============================================================
// 4. Type-erased function wrapper (mini std::function)
//    Classic void* pattern: store callable + context together
// ============================================================
class Task {
public:
    using InvokeFn = void (*)(void* context);
    using DestroyFn = void (*)(void* context);

    Task() = default;

    // Constructor for callable with captured state
    template <typename F>
    Task(F&& f) {
        using Callable = std::decay_t<F>;
        auto* ctx = new Callable(std::forward<F>(f));
        
        context_ = ctx;
        invoke_ = [](void* ctx) {
            (*static_cast<Callable*>(ctx))();
        };
        destroy_ = [](void* ctx) {
            delete static_cast<Callable*>(ctx);
        };
    }

    ~Task() {
        if (destroy_ && context_) {
            destroy_(context_);
        }
    }

    // Move semantics
    Task(Task&& other) noexcept
        : context_(other.context_), invoke_(other.invoke_), destroy_(other.destroy_) {
        other.context_ = nullptr;
        other.invoke_ = nullptr;
        other.destroy_ = nullptr;
    }

    Task& operator=(Task&& other) noexcept {
        if (this != &other) {
            if (destroy_ && context_) destroy_(context_);
            context_ = other.context_;
            invoke_ = other.invoke_;
            destroy_ = other.destroy_;
            other.context_ = nullptr;
            other.invoke_ = nullptr;
            other.destroy_ = nullptr;
        }
        return *this;
    }

    // Non-copyable (owns resources)
    Task(const Task&) = delete;
    Task& operator=(const Task&) = delete;

    void operator()() const {
        if (!invoke_) throw std::runtime_error("Task: empty task invoked");
        invoke_(context_);
    }

    explicit operator bool() const noexcept {
        return invoke_ != nullptr;
    }

private:
    void* context_ = nullptr;
    InvokeFn invoke_ = nullptr;
    DestroyFn destroy_ = nullptr;
};

// ============================================================
// 5. Heterogeneous container with iterators and move semantics
// ============================================================
class HeteroContainer {
public:
    struct Node {
        void* data;
        TypeTag tag;
        Node* next;
    };

    // Iterator for range-based for loops
    class Iterator {
    public:
        Iterator(Node* node) : current_(node) {}
        
        const Node& operator*() const { return *current_; }
        const Node* operator->() const { return current_; }
        
        Iterator& operator++() {
            current_ = current_->next;
            return *this;
        }
        
        bool operator!=(const Iterator& other) const {
            return current_ != other.current_;
        }

    private:
        Node* current_;
    };

    HeteroContainer() = default;

    ~HeteroContainer() {
        clear();
    }

    // Move constructor
    HeteroContainer(HeteroContainer&& other) noexcept
        : head_(other.head_), size_(other.size_) {
        other.head_ = nullptr;
        other.size_ = 0;
    }

    // Move assignment
    HeteroContainer& operator=(HeteroContainer&& other) noexcept {
        if (this != &other) {
            clear();
            head_ = other.head_;
            size_ = other.size_;
            other.head_ = nullptr;
            other.size_ = 0;
        }
        return *this;
    }

    // Non-copyable
    HeteroContainer(const HeteroContainer&) = delete;
    HeteroContainer& operator=(const HeteroContainer&) = delete;

    Iterator begin() { return Iterator(head_); }
    Iterator end() { return Iterator(nullptr); }

    void push_int(int v) {
        auto* node = new Node{new int(v), TypeTag::Int, head_};
        head_ = node;
        ++size_;
    }

    void push_double(double v) {
        auto* node = new Node{new double(v), TypeTag::Double, head_};
        head_ = node;
        ++size_;
    }

    void push_string(const char* s) {
        if (!s) throw std::invalid_argument("push_string: null string");
        std::size_t len = std::strlen(s) + 1;
        auto* copy = new char[len];
        std::memcpy(copy, s, len);
        auto* node = new Node{copy, TypeTag::CString, head_};
        head_ = node;
        ++size_;
    }

    void clear() {
        Node* cur = head_;
        while (cur) {
            Node* next = cur->next;
            if (cur->tag == TypeTag::CString) {
                delete[] static_cast<char*>(cur->data);
            } else {
                // Int and Double were allocated with new
                if (cur->tag == TypeTag::Int) delete static_cast<int*>(cur->data);
                else if (cur->tag == TypeTag::Double) delete static_cast<double*>(cur->data);
            }
            delete cur;
            cur = next;
        }
        head_ = nullptr;
        size_ = 0;
    }

    std::size_t size() const noexcept { return size_; }
    bool empty() const noexcept { return size_ == 0; }

private:
    Node* head_ = nullptr;
    std::size_t size_ = 0;
};

// ============================================================
// 6. Modern C++ alternatives (for comparison)
// ============================================================
template <typename T>
void safe_swap(T& a, T& b) {
    T tmp = std::move(a);
    a = std::move(b);
    b = std::move(tmp);
}

using Value = std::variant<int, double, std::string>;

void safe_print(const Value& v) {
    std::visit([](const auto& x) {
        using T = std::decay_t<decltype(x)>;
        if constexpr (std::is_same_v<T, int>)         std::cout << "int:    " << x << '\n';
        else if constexpr (std::is_same_v<T, double>) std::cout << "double: " << x << '\n';
        else                                          std::cout << "str:    " << x << '\n';
    }, v);
}

template <typename T, typename Op>
T reduce(const T* data, std::size_t n, T init, Op op) {
    for (std::size_t i = 0; i < n; ++i) init = op(init, data[i]);
    return init;
}

} // namespace voidptr_demo

// ============================================================
int main() {
    using namespace voidptr_demo;

    try {
        std::cout << "=== 1. Generic swap (exception-safe) ===\n";
        int x = 10, y = 42;
        generic_swap(&x, &y, sizeof(int));
        std::cout << "x=" << x << ", y=" << y << '\n';

        std::cout << "\n=== 2. Generic print (with validation) ===\n";
        int i = 7;
        generic_print(&i, TypeTag::Int);

        std::cout << "\n=== 3. Type-erased function wrapper ===\n";
        int counter = 0;
        Task t1 = [&counter]() { 
            counter += 10; 
            std::cout << "Task 1: counter = " << counter << '\n';
        };
        
        Task t2 = [msg = std::string("Hello from lambda")]() {
            std::cout << "Task 2: " << msg << '\n';
        };

        t1();
        t2();

        // Move semantics
        Task t3 = std::move(t1);
        t3();

        std::cout << "\n=== 4. Heterogeneous container with iterators ===\n";
        HeteroContainer container;
        container.push_int(42);
        container.push_double(3.14);
        container.push_string("test");
        container.push_int(-7);

        std::cout << "Container size: " << container.size() << '\n';
        std::cout << "Iterating:\n";
        for (const auto& node : container) {
            generic_print(node.data, node.tag);
        }

        // Move semantics
        HeteroContainer container2 = std::move(container);
        std::cout << "After move, container2 size: " << container2.size() << '\n';

        std::cout << "\n=== 5. Modern C++ alternatives ===\n";
        int sx = 10, sy = 20;
        safe_swap(sx, sy);
        std::cout << "safe_swap: sx=" << sx << ", sy=" << sy << '\n';

        std::vector<Value> values = {42, 3.14, std::string("hi")};
        for (const auto& v : values) safe_print(v);

        int nums[] = {1, 2, 3, 4, 5};
        int total = reduce(nums, 5, 0, [](int acc, int v){ return acc + v; });
        std::cout << "template reduce sum = " << total << '\n';

        std::cout << "\n=== 6. Error handling demo ===\n";
        try {
            generic_print(nullptr, TypeTag::Int);
        } catch (const std::exception& e) {
            std::cout << "Caught expected error: " << e.what() << '\n';
        }

    } catch (const std::exception& e) {
        std::cerr << "Unexpected error: " << e.what() << '\n';
        return 1;
    }

    return 0;
}
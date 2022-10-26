#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <unistd.h>
#include <netinet/ip_icmp.h>
#include <time.h>
#include <fcntl.h>
#include <signal.h>
#include <stdbool.h>

#define BUF_SIZE 64
#define PORT_NUM 0

typedef struct {
    struct icmphdr hdr;
    char data[BUF_SIZE];
} ping_data_t;

typedef struct {
    struct ip ip_hdr;
    ping_data_t ping_pkt;
} ip_data_t;

static ushort checksum(void* start, int count)
{
    ushort* addr = start;
    uint sum = 0;
    ushort checksum;
    while (count > 1)  {
        sum += *addr++;
        count -= 2;
    }
    if (count > 0) {
        sum += *addr;
    }
    while (sum >> 16) {
        sum = (sum & 0xffff) + (sum >> 16);
    }
    checksum = ~sum;
    return checksum;
}

static void prepare_icmp_pkt(ping_data_t* ping_pkt)
{
    memset(ping_pkt, 0, sizeof(ping_data_t));
    ping_pkt->hdr.type = ICMP_ECHO;
    ping_pkt->hdr.checksum = checksum(ping_pkt, sizeof(ping_data_t));
}

static ulong get_time()
{
    struct timespec time;
    clock_gettime(CLOCK_MONOTONIC, &time);
    ulong time_ms = time.tv_sec * 1000 + (time.tv_nsec / 1000000);
    return time_ms;
}

void ping_once(int sock_fd, struct sockaddr_in* dest_addr, size_t* send_count, size_t* recv_count,
        const ulong start_time, const ulong timeout)
{
    ping_data_t data;
    prepare_icmp_pkt(&data);

    if (sendto(sock_fd, (void*) &data, sizeof(ping_data_t), 0,
               (const struct sockaddr*) dest_addr, sizeof(struct sockaddr_in)) == -1) {
        return;
    }
    printf("Send packet to %s\n", inet_ntoa(dest_addr->sin_addr));
    (*send_count)++;

    bool correct = false;

    struct timeval tv;
    tv.tv_sec = timeout / 1000;
    tv.tv_usec = (timeout % 1000) * 1000;
    for (;;) {
        fd_set rfd;
        FD_ZERO(&rfd);
        FD_SET(sock_fd, &rfd);

        int n = select(sock_fd + 1, &rfd, 0, 0, &tv);
        if (n <= 0) {
            break;
        }

        if (FD_ISSET(sock_fd, &rfd)) {
            const ulong elapsed_time = (get_time() - start_time);
            if (elapsed_time > timeout) {
                break;
            } else {
                const ulong new_timeout = timeout - elapsed_time;
                tv.tv_sec = new_timeout / 1000;
                tv.tv_usec = (new_timeout % 1000) * 1000;
            }

            ip_data_t recv_pkt;
            struct sockaddr_in ret_addr;
            socklen_t ret_addr_len = sizeof(struct sockaddr_in);
            if (recvfrom(sock_fd, &recv_pkt, sizeof(ip_data_t), 0,
                         (struct sockaddr*) &ret_addr, &ret_addr_len) > 0) {
                if (dest_addr->sin_addr.s_addr == ret_addr.sin_addr.s_addr) {
                    correct = true;
                    printf("Received packet from %s\n", inet_ntoa(ret_addr.sin_addr));
                    break;
                }
            } else {
                break;
            }
        }
    }

    if (correct) {
        (*recv_count)++;
    }
}

static PyObject* ping_many_times(PyObject* self, PyObject* args) {
    char* str_addr;
    ulong timeout, interval;

    if (!PyArg_ParseTuple(args, "skk", &str_addr, &timeout, &interval)) {
        return PyLong_FromLong(EXIT_FAILURE);
    }

    timeout *= 1000;

    in_addr_t host = inet_addr(str_addr);

    struct sockaddr_in addr = {
            .sin_family = AF_INET,
            .sin_addr.s_addr = host,
            .sin_port = htons(PORT_NUM)
    };

    int sock_fd = socket(AF_INET, SOCK_RAW, IPPROTO_ICMP);

    if (sock_fd == -1) {
        printf("Unable to create raw socket. Please, provide CAP_NET_RAW privileges\n");
        return PyLong_FromLong(EXIT_FAILURE);
    }

    size_t send_count = 0, recv_count = 0;
    ulong start_time = get_time();
    for (;;) {
        if (get_time() - start_time > timeout) {
            break;
        }
        ping_once(sock_fd, &addr, &send_count, &recv_count, start_time, timeout);
        usleep(interval);
    }
    printf("Total packets sent: %ld\n", send_count);
    printf("Total packets received: %ld\n", recv_count);
    close(sock_fd);
    return PyLong_FromLong(EXIT_SUCCESS);
}

PyMODINIT_FUNC PyInit_ping() {
    static PyMethodDef methods[] = {
        {
            .ml_name = "ping",
            .ml_meth = ping_many_times,
            .ml_flags = METH_VARARGS,
            .ml_doc = "Ping to a host"
        },
        {NULL, NULL, 0, NULL}
    };

    static PyModuleDef moduleDef = {
        .m_base = PyModuleDef_HEAD_INIT,
        .m_name = "ping",
        .m_size = -1,
        .m_methods = methods,
    };

    return PyModule_Create(&moduleDef);
}


/**
 * @file
 * @brief An allocator's API for fixed-size objects.
 *
 * @author Kirill Tyushev
 * @author Eldar Abusalimov
 * @author Gleb Efimov
 */

#ifndef MEM_MISC_UTIL_POOL_H_
#define MEM_MISC_UTIL_POOL_H_


#include <stddef.h>
#include <util/macro.h>
#include <util/slist.h>

/** Representation of the pool*/
struct pool {
	/* Place in memory for allocation */
	void * memory;
	/* List of free block
	 * (this is a block, which was used,
	 * then was non-used and return to pool) */
	struct slist free_blocks;
	/* Size of object in pool (in bytes) */
	size_t obj_size;
	/* Size of pool */
	size_t pool_size;
	/* Boundary, after which begin non-allocated memory */
	void * bound_free;
};

/**
 * Create pool descriptor. The memory for pool is allocated in special section
 * "reserve.pool".
 *
 * @param name of cache
 * @param type of objects in cache
 * @param count of objects in cache
 */
#define POOL_DEF(name, object_type, size) \
	static union {                   \
		typeof(object_type) object;  \
		struct slist_link free_link; \
	} __pool_storage ## name[size]   \
	__attribute__((section(".bss.reserve.pool,\"aw\",%nobits;#")));  \
	static struct pool name = { \
			.memory = __pool_storage ## name, \
			.bound_free = __pool_storage ## name, \
			.free_blocks = SLIST_INIT(&name.free_blocks),\
			.obj_size = sizeof(*__pool_storage ## name), \
			.pool_size = sizeof(*__pool_storage ## name) * size, \
	};

/**
 * allocate single object from the cache and return it to the caller
 * @param cache corresponding to allocating object
 * @return the address of allocated object or NULL if pool is full
 */
extern void *pool_alloc(struct pool *pool);

/**
 * free an object and return it to the cache
 * @param cachep corresponding to freeing object
 * @param objp which will be free
 */
extern void pool_free(struct pool *pool, void *object);

extern int pool_belong(struct pool* pool, void* obj);

#endif /* MEM_MISC_UTIL_POOL_H_ */
